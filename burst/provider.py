# -*- coding: utf-8 -*-

"""
Provider thread methods
"""

import logging
from burst.kodi import get_setting, set_setting
from future.utils import PY3, iteritems

import os
import re
import json
import time
from .client import Client
from .filtering import cleanup_results
from .providers.definitions import definitions, longest
from .utils import ADDON_PATH, get_int, clean_size, get_alias, with_defaults
from kodi_six import xbmc, xbmcaddon, py2_encode
if PY3:
    from urllib.parse import quote, unquote, urlparse
    unicode = str
else:
    from urllib import quote, unquote, urlparse

def generate_payload(provider, generator, filtering, verify_name=True, verify_size=True):
    """ Payload formatter to format results the way Jacktook expects them

    Args:
        provider        (str): Provider ID
        generator  (function): Generator method, can be either ``extract_torrents`` or ``extract_from_api``
        filtering (Filtering): Filtering class instance
        verify_name    (bool): Whether to double-check the results' names match the query or not
        verify_size    (bool): Whether to check the results' file sizes

    Returns:
        list: Formatted results
    """
    filtering.information(provider)
    results = []

    definition = definitions[provider]
    definition = get_alias(definition, get_setting("%s_alias" % provider))

    for id, name, info_hash, uri, size, seeds, peers in generator:
        size = clean_size(size)
        # uri, info_hash = clean_magnet(uri, info_hash)
        v_name = name if verify_name else filtering.title
        v_size = size if verify_size else None
        if filtering.verify(provider, v_name, v_size):
            sort_seeds = get_int(seeds)
            sort_resolution = filtering.determine_resolution(v_name)[1]+1
            sort_balance = (sort_seeds + 1) * 3 * sort_resolution

            results.append({
                "id": id,
                "name": name,
                "uri": uri,
                "info_hash": info_hash,
                "size": size,
                "seeds": sort_seeds,
                "peers": get_int(peers),
                "language": definition["language"] if 'language' in definition else 'en',
                "provider": '[COLOR %s]%s[/COLOR]' % (definition['color'], definition['name']),
                "icon": os.path.join(ADDON_PATH, 'burst', 'providers', 'icons', '%s.png' % provider),
                "sort_resolution": sort_resolution,
                "sort_balance": sort_balance
            })
        else:
            logging.debug(filtering.reason)

    logging.debug('[%s] >>>>>> %s would send %d torrents to Jacktook <<<<<<<' % (provider, provider, len(results)))
    results = cleanup_results(results)
    logging.debug('[%s] >>>>>> %s would send %d torrents to Jacktook after cleanup <<<<<<<' % (provider, provider, len(results)))

    return results


def process(provider, generator, filtering, has_special, verify_name=True, verify_size=True, skip_auth=False, start_time=None, timeout=None):
    """ Method for processing provider results using its generator and Filtering class instance

    Args:
        provider        (str): Provider ID
        generator  (function): Generator method, can be either ``extract_torrents`` or ``extract_from_api``
        filtering (Filtering): Filtering class instance
        has_special    (bool): Whether title contains special chars
        verify_name    (bool): Whether to double-check the results' names match the query or not
        verify_size    (bool): Whether to check the results' file sizes
    """
    logging.debug("[%s] execute_process for %s with %s" % (provider, provider, repr(generator)))
    definition = definitions[provider]
    definition = with_defaults(get_alias(definition, get_setting("%s_alias" % provider)))

    client = Client(info=filtering.info, request_charset=definition['charset'], response_charset=definition['response_charset'], is_api='is_api' in definition and definition['is_api'])
    token = None
    loggingged_in = False
    token_auth = False
    used_queries = set()

    if get_setting('kodi_language', bool):
        kodi_language = xbmc.getLanguage(xbmc.ISO_639_1)
        if kodi_language:
            filtering.kodi_language = kodi_language
        language_exceptions = get_setting('language_exceptions')
        if language_exceptions.strip().lower():
            filtering.language_exceptions = re.split(r',\s?', language_exceptions)

    logging.debug("[%s] Queries: %s" % (provider, filtering.queries))
    logging.debug("[%s] Extras:  %s" % (provider, filtering.extras))

    last_priority = 1
    for query, extra, priority in zip(filtering.queries, filtering.extras, filtering.queries_priorities):
        logging.debug("[%s] Before keywords - Query: %s - Extra: %s" % (provider, repr(query), repr(extra)))
        if has_special:
            # Removing quotes, surrounding {title*} keywords, when title contains special chars
            query = re.sub("[\"']({title.*?})[\"']", '\\1', query)

        query = filtering.process_keywords(provider, query, definition)
        extra = filtering.process_keywords(provider, extra, definition)

        if not query:
            continue
        elif query+extra in used_queries:
            # Make sure we don't run same query for this provider
            continue
        elif priority > last_priority and filtering.results:
            # Skip fallbacks if there are results
            logging.debug("[%s] Skip fallback as there are already results" % provider)
            continue
        elif start_time and timeout and time.time() - start_time + 3 >= timeout:
            # Stop doing requests if there is 3 seconds left for the overall task
            continue

        used_queries.add(query+extra)
        last_priority = priority

        try:
            if 'charset' in definition and definition['charset'] and 'utf' not in definition['charset'].lower():
                query = quote(query.encode(definition['charset']))
                extra = quote(extra.encode(definition['charset']))
            else:
                query = quote(py2_encode(query))
                extra = quote(py2_encode(extra))
        except Exception as e:
            logging.debug("[%s] Could not quote the query (%s): %s" % (provider, query, e))
            pass

        logging.debug("[%s] After keywords  - Query: %s - Extra: %s" % (provider, repr(query), repr(extra)))
        if not query:
            return filtering.results

        url_search = filtering.url.replace('QUERY', query)
        url_search = url_search.replace('EXTRA', extra)

        url_search = url_search.replace(' ', definition['separator'])
        if definition['separator'] != '%20':
            url_search = url_search.replace('%20', definition['separator'])

        # MagnetDL fix...
        url_search = url_search.replace('FIRSTLETTER', query[:1])

        # Creating the payload for POST method
        if 'post_data' in definition and not filtering.post_data:
            filtering.post_data = eval(definition['post_data'])

        payload = dict()
        for key, value in iteritems(filtering.post_data):
            payload[key] = filtering.post_data[key].replace('QUERY', query)
            payload[key] = payload[key].replace('EXTRA', extra)
            payload[key] = unquote(payload[key])

        # Creating the payload for GET method (unused at the moment)
        data = None
        if filtering.get_data:
            data = dict()
            for key, value in iteritems(filtering.get_data):
                data[key] = filtering.get_data[key].replace('QUERY', query)
                data[key] = data[key].replace('EXTRA', extra)
                data[key] = unquote(data[key])

        logging.debug("-   %s query: %s" % (provider, repr(query)))
        logging.debug("--  %s url_search before token: %s" % (provider, repr(url_search)))
        logging.debug("--- %s using POST payload: %s" % (provider, repr(payload)))
        logging.debug("----%s filtering with post_data: %s" % (provider, repr(filtering.post_data)))

        # Set search's "title" in filtering to double-check results' names
        if 'filter_title' in definition and definition['filter_title']:
            filtering.filter_title = True
            filtering.title = query

        if 'initial_url' in definition and definition['initial_url']:
            url = definition['initial_url']
            if not url.startswith('http'):
                url = definition['root_url'] + url
            client.open(url)

        if token:
            logging.info('[%s] Reusing existing token' % provider)
            url_search = url_search.replace('TOKEN', token)
        elif 'token' in definition:
            token_url = definition['base_url'] + definition['token']
            logging.debug("[%s] Getting token for %s at %s" % (provider, provider, repr(token_url)))
            client.open(py2_encode(token_url))
            try:
                token_data = json.loads(client.content)
            except:
                logging.error('%s: Failed to get token for %s' % (provider, repr(url_search)))
                return filtering.results
            logging.debug("[%s] Token response for %s: %s" % (provider, provider, repr(token_data)))
            if 'token' in token_data:
                token = token_data['token']
                logging.debug("[%s] Got token for %s: %s" % (provider, provider, repr(token)))
                url_search = url_search.replace('TOKEN', token)
            else:
                logging.warning('%s: Unable to get token for %s' % (provider, repr(url_search)))

        if loggingged_in:
            logging.info("[%s] Reusing previous loggingin" % provider)
        elif token_auth:
            logging.info("[%s] Reusing previous token authorization" % provider)
        elif 'private' in definition and definition['private']:
            username = get_setting('%s_username' % provider, unicode)
            password = get_setting('%s_password' % provider, unicode)
            passkey = get_setting('%s_passkey' % provider, unicode)
            if not username and not password and not passkey:
                for addon_name in ('script.magnetic.%s' % provider, 'script.magnetic.%s-mc' % provider):
                    for setting in ('username', 'password'):
                        try:
                            value = xbmcaddon.Addon(addon_name).getSetting(setting)
                            set_setting('%s_%s' % (provider, setting), value)
                            if setting == 'username':
                                username = value
                            if setting == 'password':
                                password = value
                        except:
                            pass

            if username:
                client.username = username
                url_search = url_search.replace('USERNAME', username)

            if passkey:
                client.passkey = passkey
                url_search = url_search.replace('PASSKEY', passkey)

            elif 'loggingin_object' in definition and definition['loggingin_object']:
                loggingin_object = None
                loggingin_headers = None
                loggingged_in = skip_auth

                try:
                    loggingin_object = definition['loggingin_object'].replace('USERNAME', 'u"%s"' % username).replace('PASSWORD', 'u"%s"' % password)
                except Exception as e:
                    logging.error("Could not make loggingin object for %s: %s" % (provider, e))
                try:
                    if 'loggingin_headers' in definition and definition['loggingin_headers']:
                        loggingin_headers = eval(definition['loggingin_headers'])
                except Exception as e:
                    logging.error("Could not make loggingin headers for %s: %s" % (provider, e))

                # TODO generic flags in definitions for those...
                if 'csrf_token' in definition and definition['csrf_token']:
                    client.open(definition['root_url'] + definition['loggingin_path'])
                    if client.content:
                        csrf_token = re.search(r'name=\"_?csrf_token\" value=\"(.*?)\"', client.content)
                        if csrf_token:
                            loggingin_object = loggingin_object.replace('CSRF_TOKEN', '"%s"' % csrf_token.group(1))
                        else:
                            loggingged_in = True

                if not logged_in and 'login_cookie' in definition and definition['login_cookie']:
                    cookie_domain = '{uri.netloc}'.format(uri=urlparse(definition['root_url']))
                    cookie_domain = re.sub('www\d*\.', '', cookie_domain)

                    client._read_cookies()
                    if client.cookie_exists(definition['login_cookie'], urlparse(definition['root_url']).netloc):
                        logged_in = True
                        log.info("[%s] Using Cookie sync for authentication" % (provider))

                if 'token_auth' in definition:
                    # logging.debug("[%s] loggingging in with: %s" % (provider, loggingin_object))
                    if client.open(definition['root_url'] + definition['token_auth'], post_data=eval(loggingin_object)):
                        try:
                            token_data = json.loads(client.content)
                        except:
                            logging.error('%s: Failed to get token from %s' % (provider, definition['token_auth']))
                            return filtering.results
                        logging.debug("[%s] Token response for %s: %s" % (provider, provider, repr(token_data)))
                        if 'token' in token_data:
                            client.token = token_data['token']
                            logging.debug("[%s] Auth token for %s: %s" % (provider, provider, repr(client.token)))
                        else:
                            logging.error('[%s] Unable to get auth token for %s' % (provider, repr(url_search)))
                            return filtering.results
                        logging.info('[%s] Token auth successful' % provider)
                        token_auth = True
                    else:
                        logging.error("[%s] Token auth failed with response: %s" % (provider, repr(client.content)))
                        return filtering.results
                elif not loggingged_in and client.loggingin(definition['root_url'], definition['loggingin_path'],
                                                    eval(loggingin_object), loggingin_headers, definition['loggingin_failed'], definition['loggingin_prerequest']):
                    logging.info('[%s] loggingin successful' % provider)
                    loggingged_in = True
                elif not loggingged_in:
                    logging.error("[%s] loggingin failed: %s", provider, client.status)
                    logging.debug("[%s] Failed loggingin content: %s", provider, repr(client.content))
                    return filtering.results

                if loggingged_in:
                    if provider == 'hd-torrents':
                        client.open(definition['root_url'] + '/torrents.php')
                        csrf_token = re.search(r'name="csrfToken" value="(.*?)"', client.content)
                        if csrf_token:
                            url_search = url_search.replace("CSRF_TOKEN", csrf_token.group(1))
                    client.save_cookies()

        logging.info("[%s] >  %s search URL: %s" % (provider, definition['name'].rjust(longest), url_search))

        headers = None
        if 'headers' in definition and definition['headers']:
            headers = eval(definition['headers'])
            logging.info("[%s] >  %s headers: %s" % (provider, definition['name'].rjust(longest), headers))

        client.open(py2_encode(url_search), post_data=payload, get_data=data, headers=headers)
        try:
            filtering.results.extend(
                generate_payload(provider,
                                generator(provider, client),
                                filtering,
                                verify_name,
                                verify_size))
        except Exception as e:
            logging.error("[%s] Error from payload generator: %s", provider, e)
    return filtering.results

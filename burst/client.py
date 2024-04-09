# -*- coding: utf-8 -*-

"""
Burst web client
"""

import logging
from burst.kodi import get_setting
from future.utils import PY3, iteritems

import re
import os
import urllib3
import dns.resolver
import requests

from time import sleep
from urllib3.util import connection
from .utils import encode_dict, translatePath
if PY3:
    from http.cookiejar import LWPCookieJar
    from urllib.parse import urlparse, urlencode
    unicode = str
else:
    from cookielib import LWPCookieJar
    from urllib import urlencode
    from urlparse import urlparse

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
if os.name == 'nt':
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
PATH_TEMP = translatePath("special://temp")

# Custom DNS default data
dns_cache = {}
dns_public_list = ['9.9.9.9', '8.8.8.8', '8.8.4.4']
dns_opennic_list = ['163.172.168.171', '152.70.189.130', '167.86.112.174']
# Save original DNS resolver
_orig_create_connection = connection.create_connection

# Proxy types
proxy_types = ["socks4",  # socks4 (hostname resolve on client)
    "socks5",  # socks5 (hostname resolve on client)
    "http",
    "https",
    "socks4a",  # socks4 latest version with hostname resolve by proxy
    "socks5h"]  # socks5 latest version with hostname resolve by proxy

# Disable warning from urllib
urllib3.disable_warnings()

# Kodi settings
public_dns_list = get_setting("public_dns_list", unicode)
opennic_dns_list = get_setting("opennic_dns_list", unicode)
proxy_enabled = get_setting("proxy_enabled", bool)
proxy_use_type = get_setting("proxy_use_type", int)
proxy_host = get_setting("proxy_host", unicode)
proxy_port = get_setting("proxy_port", int)
proxy_loggingin = get_setting("proxy_login", unicode)
proxy_password = get_setting("proxy_password", unicode)
proxy_type = get_setting("proxy_type", int)
use_public_dns = get_setting("use_public_dns", bool)
use_tor_dns = get_setting("use_tor_dns", bool)

def MyResolver(host):
    if '.' not in host:
        return host

    try:
        return dns_cache[host]
    except KeyError:
        pass

    ip = ResolvePublic(host)
    if not ip:
        ip = ResolveOpennic(host)

    if ip:
        logging.debug("Host %s resolved to %s" % (host, ip))
        dns_cache[host] = ip
        return ip
    else:
        return host

def ResolvePublic(host):
    try:
        logging.debug("Custom DNS resolving with public DNS for: %s" % host)
        resolver = dns.resolver.Resolver()
        resolver.nameservers = dns_public_list
        answer = resolver.query(host, 'A')
        return answer.rrset.items[0].address
    except:
        return

def ResolveOpennic(host):
    try:
        logging.debug("Custom DNS resolving with public DNS for: %s" % host)
        resolver = dns.resolver.Resolver()
        resolver.nameservers = dns_opennic_list
        answer = resolver.query(host, 'A')
        return answer.rrset.items[0].address
    except:
        return

class Client:
    """
    Web client class with automatic charset detection and decoding
    """
    def __init__(self, info=None, request_charset='utf-8', response_charset=None, is_api=False):
        self._counter = 0
        self._cookies_filename = ''
        self._cookies = LWPCookieJar()
        self.url = None
        self.user_agent = USER_AGENT
        self.content = None
        self.status = None
        self.username = None
        self.token = None
        self.passkey = None
        self.info = info
        self.proxy_url = None
        self.request_charset = request_charset
        self.response_charset = response_charset
        self.is_api = is_api

        self.needs_proxylock = False

        self.headers = dict()
        self.request_headers = None

        self.session = requests.session()
        self.session.verify = False

        # Enabling retrying on failed requests
        retries = Retry(
            total=3,
            read=2,
            connect=2,
            redirect=3,
            backoff_factor=0.2,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        # self.session = cfscrape.create_scraper()
        # self.scraper = cfscrape.create_scraper()
        # self.session = self.scraper.session()

        global dns_public_list
        global dns_opennic_list
        dns_public_list = public_dns_list.replace(" ", "").split(",")
        dns_opennic_list = opennic_dns_list.replace(" ", "").split(",")
        # socket.setdefaulttimeout(60)

        # Parsing proxy information
        proxy = {
            'enabled': proxy_enabled,
            'use_type': proxy_use_type,
            'type': proxy_types[0],
            'host': proxy_host,
            'port': proxy_port,
            'loggingin': proxy_loggingin,
            'password': proxy_password,
        }

        try:
            proxy['type'] = proxy_types[proxy_type]
        except:
            pass

        if use_public_dns:
            connection.create_connection = patched_create_connection

        if proxy['enabled']:
            if proxy['use_type'] == 0 and info and "proxy_url" in info:
                logging.debug("Setting proxy from Jacktook: %s" % (info["proxy_url"]))

                self.proxy_url = info["proxy_url"]
            elif proxy['use_type'] == 1:
                logging.debug("Setting proxy with custom settings: %s" % (repr(proxy)))

                if proxy['loggingin'] or proxy['password']:
                    self.proxy_url = "{0}://{1}:{2}@{3}:{4}".format(proxy['type'], proxy['loggingin'], proxy['password'], proxy['host'], proxy['port'])
                else:
                    self.proxy_url = "{0}://{1}:{2}".format(proxy['type'], proxy['host'], proxy['port'])

            if self.proxy_url:
                self.session.proxies = {
                    'http': self.proxy_url,
                    'https': self.proxy_url,
                }

    def _create_cookies(self, payload):
        return urlencode(payload)

    def _locate_cookies(self, url=''):
        cookies_path = os.path.join(PATH_TEMP, 'burst')
        if not os.path.exists(cookies_path):
            try:
                os.makedirs(cookies_path)
            except Exception as e:
                logging.debug("Error creating cookies directory: %s" % repr(e))

        return os.path.join(cookies_path, 'common_cookies.jar')

    def _read_cookies(self, url=''):
        self._cookies_filename = self._locate_cookies(url)
        if os.path.exists(self._cookies_filename):
            try:
                self._cookies.load(self._cookies_filename)
            except Exception as e:
                logging.debug("Reading cookies error: %s" % repr(e))

    def save_cookies(self):
        self._cookies_filename = self._locate_cookies(self.url)

        try:
            self._cookies.save(self._cookies_filename)
        except Exception as e:
            logging.debug("Saving cookies error: %s" % repr(e))

    def _good_spider(self):
        self._counter += 1
        if self._counter > 1:
            sleep(0.25)

    def cookies(self):
        """ Saved client cookies

        Returns:
            list: A list of saved Cookie objects
        """
        return self._cookies

    def open(self, url, language='en', post_data=None, get_data=None, headers=None):
        """ Opens a connection to a webpage and saves its HTML content in ``self.content``

        Args:
            url        (str): The URL to open
            language   (str): The language code for the ``Content-Language`` header
            post_data (dict): POST data for the request
            get_data  (dict): GET data for the request
        """

        if get_data:
            url += '?' + urlencode(get_data)

        logging.debug("Opening URL: %s" % repr(url))
        if self.session.proxies:
            logging.debug("Proxies: %s" % (repr(self.session.proxies)))

        self._read_cookies(url)
        self.session.cookies = self._cookies

        # logging.debug("Cookies for %s: %s" % (repr(url), repr(self._cookies)))

        # Default headers for any request. Pretend like we are the usual browser.
        req_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6,pl;q=0.5',
            'Cache-Control': 'max-age=0',
            'Content-Language': language,
            'Origin': url,
            'Referer': url,
            'User-Agent': self.user_agent
        }

        # Remove referer for API providers
        if self.is_api:
            del req_headers['Referer']

        # If headers passed to open() call - we overwrite headers.
        if headers:
            for key, value in iteritems(headers):
                if key == ':path':
                    u = urlparse(url)
                    value = u.path
                if value:
                    req_headers[key] = value
                elif key.capitalize() in req_headers:
                    del req_headers[key.capitalize()]

        if self.token:
            req_headers["Authorization"] = self.token

        req = None
        if post_data:
            req = requests.Request('POST', url, data=post_data, headers=req_headers)
        else:
            req = requests.Request('GET', url, headers=req_headers)

        prepped = self.session.prepare_request(req)
        self.request_headers = prepped.headers

        try:
            self._good_spider()
            with self.session.send(prepped) as response:
                self.headers = response.headers
                self.status = response.status_code
                self.url = response.url

                if self.response_charset:
                    self.content = response.content.decode(self.response_charset, 'ignore')
                else:
                    self.content = response.text

        except requests.exceptions.InvalidSchema as e:
            # If link points to a magnet: then it can be used as a content
            matches = re.findall('No connection adapters were found for \'(.*?)\'', str(e))
            if matches:
                self.content = matches[0]
                return True

            import traceback
            logging.error("%s failed with %s:" % (repr(url), repr(e)))
            map(logging.debug, traceback.format_exc().split("\n"))
        except Exception as e:
            import traceback
            logging.error("%s failed with %s:" % (repr(url), repr(e)))
            map(logging.debug, traceback.format_exc().split("\n"))

        logging.debug("Status for %s : %s" % (repr(url), str(self.status)))

        return self.status == 200

    def loggingin(self, root_url, url, data, headers, fails_with, prerequest=None):
        """ loggingin wrapper around ``open``

        Args:
            url        (str): The URL to open
            data      (dict): POST loggingin data
            fails_with (str): String that must **not** be included in the response's content

        Returns:
            bool: Whether or not loggingin was successful
        """
        if not url.startswith('http'):
            url = root_url + url

        if prerequest:
            logging.debug("Running prerequest to %s" % (prerequest))
            self.open(prerequest.encode('utf-8'), headers=headers)

        if self.open(url.encode('utf-8'), post_data=encode_dict(data, self.request_charset), headers=headers):
            try:
                if fails_with and fails_with in self.content:
                    self.status = 'Wrong username or password'
                    return False
            except Exception as e:
                logging.debug("loggingin failed with: %s" % e)
                try:
                    if fails_with in self.content.decode('utf-8'):
                        self.status = 'Wrong username or password'
                        return False
                except:
                    return False

            return True

        return False

def patched_create_connection(address, *args, **kwargs):
    """Wrap urllib3's create_connection to resolve the name elsewhere"""
    # resolve hostname to an ip address; use your own
    # resolver here, as otherwise the system resolver will be used.
    host, port = address
    logging.debug("Custom resolver: %s --- %s --- %s" % (host, port, repr(address)))
    hostname = MyResolver(host)

    return _orig_create_connection((hostname, port), *args, **kwargs)

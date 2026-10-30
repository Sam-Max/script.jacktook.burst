# -*- coding: utf-8 -*-

import logging
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "resources", "site-packages")
)

from burst.burst import search
from jacktook.provider_base import Provider, ProviderResult
from burst.client import Client


def build_payload(**kwargs):
    payload = {
        "silent": False,
        "skip_auth": False,
    }
    payload.update(kwargs)
    return payload


def normalize_titles(title, titles):
    """Jacktook may pass an empty string or a dict of translations.

    Burst's search() expects a dict with lower-case language keys.
    """
    if isinstance(titles, dict) and titles:
        return {k.lower(): v for k, v in titles.items()}
    return {"source": title, "original": title}


def general_payload(query, silent=False):
    return build_payload(query=query, silent=silent)


def movie_payload(id, title, titles, year, silent=False):
    return build_payload(
        imdb_id=id,
        title=title,
        titles=normalize_titles(title, titles),
        year=year,
        silent=silent,
    )


def show_payload(id, title, titles, year, silent=False):
    return build_payload(
        imdb_id=id,
        title=title,
        titles=normalize_titles(title, titles),
        year=year,
        silent=silent,
    )


def season_payload(id, title, season, titles, year, silent=False):
    return build_payload(
        imdb_id=id,
        title=title,
        titles=normalize_titles(title, titles),
        season=season,
        year=year,
        silent=silent,
    )


def episode_payload(id, title, season, episode, titles, year, silent=False):
    return build_payload(
        imdb_id=id,
        title=title,
        titles=normalize_titles(title, titles),
        season=season,
        episode=episode,
        year=year,
        silent=silent,
    )


def to_provider_results(obj):
    return [
        ProviderResult(
            title=item["name"],
            indexer=item["provider"],
            guid=item["uri"],
            quality="",
            seeders=item["seeds"],
            peers=item["peers"],
            size=item["size"] if len(item["size"]) > 0 else 0,
        )
        for item in obj
    ]


class JacktookProvider(Provider):
    def search(self, query, silent=False):
        s = search(general_payload(query, silent), "general")
        return to_provider_results(s)

    def search_movie(self, id, title, titles="", year="", silent=False):
        logging.debug("search_movie")
        s = search(movie_payload(id, title, titles, year, silent), "movie")
        results = to_provider_results(s)
        logging.debug(results)
        return results

    def search_show(self, id, title, titles="", year="", silent=False):
        logging.debug("search_show")
        s = search(show_payload(id, title, titles, year, silent), "season")
        results = to_provider_results(s)
        logging.debug(results)
        return results

    def search_season(self, id, title, season_number, titles="", year="", silent=False):
        s = search(
            season_payload(id, title, season_number, titles, year, silent), "season"
        )
        return to_provider_results(s)

    def search_episode(
        self,
        id,
        title,
        season_number,
        episode_number,
        titles="",
        year="",
        silent=False,
    ):
        s = search(
            episode_payload(
                id, title, season_number, episode_number, titles, year, silent
            ),
            "episode",
        )
        return to_provider_results(s)

    def resolve(self, provider_data):
        if isinstance(provider_data, dict):
            return provider_data["url"]
        raise NotImplementedError("Resolve method can't be called on this provider")


def clear_cookies():
    client = Client()
    cookies = client._locate_cookies()
    logging.info("Removing cookies from %s" % (cookies))
    if os.path.isfile(cookies):
        os.remove(cookies)
        logging.info("Successfully removed cookies file")


action = None
if len(sys.argv) >= 2:
    action = sys.argv[1]

if action and "clear_cookies" in action:
    clear_cookies()
else:
    JacktookProvider().register()

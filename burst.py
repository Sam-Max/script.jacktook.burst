# -*- coding: utf-8 -*-

import logging
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "resources", "site-packages")
)

from burst.burst import search
from jacktook.provider import Provider, ProviderResult
from burst.client import Client


def general_payload(query):
    return {
        "silent": False,
        "skip_auth": False,
        "query": query,
    }


def movie_payload(imdb_id, title, year, titles=""):
    return {
        "silent": False,
        "skip_auth": False,
        "imdb_id": imdb_id,
        "title": title,
        "titles": titles,
        "year": year,
    }



def tv_payload(imdb_id, title, titles="", season=None, episode=None, year=None):
    return {
        "silent": False,
        "skip_auth": False,
        "imdb_id": imdb_id,
        "title": title,
        "titles": titles,
        "season": season,
        "episode": episode,
        "year": year,
    }

def season_payload(imdb_id, title, season, titles="", year=None):
    return {
        "silent": False,
        "skip_auth": False,
        "imdb_id": imdb_id,
        "title": title,
        "titles": titles,
        "season": season,
        "year": year,
    }

def episode_payload(imdb_id, title, season, episode, titles="", year=None):
    return {
        "silent": False,
        "skip_auth": False,
        "imdb_id": imdb_id,
        "title": title,
        "titles": titles,
        "season": season,
        "episode": episode,
        "year": year,
    }


def convert_results_jacktook(obj):
    result = []
    for item in obj:
        result.append(
            ProviderResult(
                title=item["name"],
                indexer=item["provider"],
                guid=item["uri"],
                quality="",
                seeders=item["seeds"],
                peers=item["peers"],
                size=item["size"] if len(item["size"]) > 0 else 0,
            )
        )
    return result


class RajadaJacktookProvider(Provider):
    def search(self, query):
        s = search(general_payload(query), "general")
        s = convert_results_jacktook(s)
        return s

    def search_movie(self, imdb_id, title, titles, year):
        s = search(movie_payload(imdb_id, title, year), "movie")
        s = convert_results_jacktook(s)
        return s

    def search_show(self, imdb_id, show_title, titles, year):
        s = search(
            tv_payload(imdb_id, show_title, year=year), "season"
        )
        s = convert_results_jacktook(s)
        return s

    def search_season(self, imdb_id, show_title, season_number, titles):
        s = search(
            season_payload(imdb_id, show_title, season_number), "season"
        )
        s = convert_results_jacktook(s)
        return s

    def search_episode(
        self, imdb_id, show_title, season_number, episode_number, titles
    ):
        s = search(
            episode_payload(imdb_id, show_title, season_number, episode_number), "episode"
        )
        s = convert_results_jacktook(s)
        return s

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
    RajadaJacktookProvider().register()

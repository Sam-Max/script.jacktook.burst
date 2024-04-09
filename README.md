# Jacktook Burst, a fork of Elementum Burst adapted for using on [Jacktook](https://github.com/Sam-Max/plugin.video.jacktook) Addon


### Features
- Fast, very fast
- Compatible with Magnetic/Magnetizer, but **disable the Quasar/Elementum Connector**
- Can extract providers, parsers and settings from Magnetic
- No extra add-ons to install, all providers are included
- No extra service running in the background
- Easy settings to enable or disable providers and filters
- First-class support with Jacktook, and only Jacktook (ask if you want to adapt to your addon)
- Simple definitions-based architecture with overrides
- Clean, PEP8 compliant code


### Installation

**IMPORTANT: Disable the Magnetic Quasar/Elementum Connector before anything else.**

Install the add-on and enjoy.

Detailed documentation available at https://quasar-burst.readthedocs.io (old)

### Adding / editing providers

**Do NOT add definitions to the `definitions.json` file**, it is generated
automatically by the Magnetic extraction script.

Default fixes and overrides are located in `burst/providers/definitions.py`, and
although you can edit that file directly, keep in mind that you will lose your
changes on the next update. You can override existing definitions by adding
another file named `overrides.py` in your profile folder, ie. in
`~/.kodi/userdata/addon_data/script.jacktook.burst/overrides.py`. Put all your
overrides in the `overrides` variable within that file, as such:
```
overrides = {
    'torlock': {
        'name': 'MyTorLock'
    }
}
```

Adding a custom provider is similar, although you'll be using a JSON file, per
provider or with all your custom providers, unless you add them all in your
custom `overrides.py`, which also works. Simply create a file with the `.json`
extension under the `providers` folder in your profile, ie. in
`~/.kodi/userdata/addon_data/script.jacktook.burst/providers/nice_provider.json`
and make sure it follows the format below (hopefully with `"subpage": false`):
```
{
    "1337x": {
        "anime_extra": "",
        "anime_keywords": "{title} {episode}",
        "anime_query": "EXTRA",
        "base_url": "http://www.1337x.to/search/QUERY/1/",
        "color": "FFF14E13",
        "general_extra": "",
        "general_keywords": "{title}",
        "general_query": "EXTRA",
        "language": null,
        "login_failed": "",
        "login_object": "",
        "login_path": null,
        "movie_extra": "",
        "movie_keywords": "{title} {year}",
        "movie_query": "EXTRA",
        "name": "1337x",
        "parser": {
            "infohash": "",
            "name": "item('a', order=2)",
            "peers": "item(tag='td', order=3)",
            "row": "find_once(tag='body').find_all('tr')",
            "seeds": "item(tag='td', order=2)",
            "size": "item(tag='td', order=5)",
            "torrent": "item(tag='a', attribute='href', order=2)"
        },
        "private": false,
        "season_extra": "",
        "season_extra2": "",
        "season_keywords": "{title} Season {season:2}",
        "season_keywords2": "{title} Season{season}",
        "season_query": "EXTRA",
        "separator": "+",
        "show_query": "",
        "subpage": true,
        "tv_extra": "",
        "tv_extra2": "",
        "tv_keywords": "{title} s{season:2}e{episode:2}",
        "tv_keywords2": "",
        "tv_keywords3": "",
        "tv_keywords_fallback": "",
        "tv_keywords_fallback2": ""
    }
}
```


### Credits
- @elgatito for Elementum Burst
- @scakemyer for initial Quasar Burst module!
- @mancuniancol for all his work on Magnetic, this add-on wouldn't have been
  possible without him.
- All the alpha and beta testers that led to the first stable release.

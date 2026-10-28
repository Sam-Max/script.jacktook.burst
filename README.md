# Jacktook Burst

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Kodi 19+](https://img.shields.io/badge/Kodi-19%2B-17B2E7.svg)](https://kodi.tv)

**Jacktook Burst is the torrent provider engine for [Jacktook](https://github.com/Sam-Max/plugin.video.jacktook) on Kodi.** It searches 84 tracker definitions in parallel and returns magnet links and `.torrent` URLs to Jacktook, which resolves and plays them. Burst never plays anything by itself.

It is a fork of [Elementum Burst](https://github.com/elgatito/script.elementum.burst), adapted to Jacktook's provider API.

| | |
|---|---|
| **Role** | Provider engine: search only, no playback |
| **Runs on** | Kodi 19+ (Python 3) |
| **Providers** | 84 definitions: 47 public, 37 private |
| **Search methods** | General, movie, show, season, episode, anime |
| **License** | MIT |

## Quick start

Requirements: Kodi 19 or newer and the [Jacktook](https://github.com/Sam-Max/plugin.video.jacktook) addon. Burst feeds Jacktook; without it there is nothing to receive the results.

### Install from the Jacktook repository (recommended)

1. Install the **Jacktook Repository** if you have not already.
2. Go to **Add-ons → Install from repository → Jacktook Repository**.
3. Select **Program add-ons → Jacktook Burst → Install**.

### Install from ZIP

1. Download `script.jacktook.burst-*.zip` from [Releases](https://github.com/Sam-Max/script.jacktook.burst/releases).
2. In Kodi, open **Add-ons → Install from zip file** (enable *Unknown sources* first if Kodi asks).
3. Select the downloaded ZIP.

Verify the install: open **Add-ons → Program add-ons**, open Jacktook Burst settings and confirm the provider list loads.

## How it works

```
Jacktook ──payload──▶ Burst ──one thread per provider──▶ trackers
                         │
                         ▼
             filter → dedupe → sort → ProviderResult[]
```

1. Jacktook sends a payload with the title, translated titles, year, IMDb id and, when applicable, season and episode.
2. Burst keeps the providers enabled for that content type and starts one thread per provider, all bounded by a single timeout.
3. Each provider is scraped through its JSON definition (parser expressions over HTML) or queried through its JSON API.
4. Results are filtered by resolution, video quality, size, keywords and language, deduplicated by info hash, sorted, capped per provider and returned as `ProviderResult(title, indexer, guid, seeders, peers, size)`.

## Configuration

Settings live under **Add-ons → Program add-ons → Jacktook Burst → Settings**.

| Category | What you control |
|---|---|
| **General** | Public DNS resolution (with public and OpenNIC server lists), Tor domain aliases, overrides folder, size range in GB, max results per provider (default 10), sort order (Resolution, Seeds, Size or Balanced), timeout (default 25 s, auto-adjusted), custom user agent |
| **Cookie sync** | Optional encrypted cookie sync through a GitHub Gist, for trackers whose session cookies expire |
| **Public trackers [A .. M]** and **[N .. ]** | Enable providers, set a per-provider domain alias and restrict each one to Movies, Shows or All |
| **Private trackers [A .. M]** and **[N .. ]** | Same controls plus username/password (or passkey) for each tracker |
| **Filtering** | Require resolution, keywords, release type or size; allow results with zero seeders |
| **Resolution** | Keep or drop 4K, 2K, 1080p, 720p, 480p, 240p |
| **Video quality** | Keep or drop BRRip, WEB-DL, HDRip, HDTV, DVD, DVDScr, Screener, 3D, Telesync, CAM, TVRip, IPTVRip, VHSRip, Trailer, Workprint, LINE |
| **Proxy** | Reuse Jacktook proxy settings, custom SOCKS4/5 or HTTP(S) proxy, or Antizapret (Russia) |
| **Advanced** | Per-content size limits, Accept/Block keyword lists (any match) and Require list (all must match), quote filtering, Kodi language matching, anime title source, parser debug logging |
| **Maintenance** | Remove stored cookies |

Private trackers require an account on each site. Enabling a private provider without valid credentials only adds failed logins to the log.

## Providers

| Type | Count | How it is fetched |
|---|---|---|
| Public (HTML) | 41 | Scraped with the provider's parser expressions |
| Public (API) | 6 | JSON API endpoints |
| Private | 37 | Login required; one of them (FileList) uses a JSON API |

<details>
<summary><strong>Public providers (47)</strong></summary>

1337x, AniDUB, AniLibria, AniMaunt, BitSearch, BT4G, Corsaro.red, Cpasbien, ETTV, ExtraNet, ExtraTorrent, EZTV, Filebase, GloTorrents, idope, Il Corsaro Nero, iTorrent, KickAss, Knaben, LE-Production, LimeTorrents, MagnetDL, MegaPeer, NewStudio.TV, Nyaa, PiratBit, RARBG, RuTor, Serialz.tv, Sky torrents, SUMOTorrent, The Pirate Bay, TNTVillage, TorLock, Torrent.by, Torrent9, TorrentDownloads, TorrentFunk, TorrentGalaxy, Torrentio, TorrentZ, Torrentz2K, UIndex, World Wide Torrents, YourBitTorrent, YTS, Zooqle

</details>

<details>
<summary><strong>Private providers (37)</strong></summary>

0day, 3d-tracker.ru, Animelayer, ArabP2P, BaibaKo.TV, bitHUmen, BitNova, BlueBird, electroTorrent, FileList, FileTracker.PL, GimmePeers, HD Torrents, helltorrents, Il Corsaro Blu, IPTorrents, Linkomanija, LostFilm, MVGroup, nCore, Nitro.To, NNM-Club, Rustorka, RuTracker, tfile.me, Torrent.lt, torrent3d.ru, TorrentDay, TorrentLeech, UHDBits, XtremeZone, YggTorrent, Zamunda, Zelka, Ztracker.cc, Гуртом, Кинозал

</details>

API-based providers: AniLibria, Corsaro.red, FileList, RARBG, Torrentio, Torrentz2K and YTS.

Trackers change domains and markup constantly. A provider that returns nothing is usually a broken definition, not a bug in the engine — open an issue with the tracker name.

## Custom providers and overrides

Definitions are data, not code. Three ways to change them:

| Location | Effect |
|---|---|
| `addon_data/script.jacktook.burst/providers/*.json` | Adds new providers and force-enables them |
| `addon_data/script.jacktook.burst/overrides.json` (or the folder set in **General → Overrides folder**) | Deep-merges changes into built-in definitions |
| `addon_data/script.jacktook.burst/overrides.py` | Python overrides exposing an `overrides` dict |

A definition has these essential fields:

| Field | Purpose |
|---|---|
| `id`, `name` | Unique provider id and display name |
| `base_url` | Search URL template |
| `private` | Requires login fields (`login_path`, `login_object`, `login_failed`) |
| `languages` | Comma-separated language codes |
| `charset` | Page encoding, when it is not UTF-8 |
| `*_keywords` | Query templates per content type, e.g. `{title:original:en} {year}` |
| `parser` | Extraction rules: `row`, `name`, `seeds`, `peers`, `size`, `torrent` or `infohash` |
| `is_api`, `api_format` | API-based provider instead of HTML scraping |
| `public_dns_alias`, `tor_dns_alias` | Alternate domains for blocked or filtered regions |

## Project layout

```
burst.py                      Jacktook entry point: payload builders and provider registration
burst/
  burst.py                    Search orchestration, provider threads, result collection
  provider.py                 Scraping pipeline (HTML and API providers)
  filtering.py                Resolution, quality, size, keyword and language filters
  normalize.py                Title and release-name normalization
  client.py                   HTTP client, cookies, proxies, retries
  providers/providers.json    84 tracker definitions
  parser/                     HTML parser inherited from Elementum
resources/settings.xml        Generated Kodi settings
resources/language/           16 translated string catalogs
scripts/                      Maintenance and settings-generation scripts
```

## Development

```bash
# Lint (config in setup.cfg)
python3 -m flake8

# Regenerate resources/settings.xml from providers.json
python3 scripts/generate_settings.py
```

`generate_settings.py` still imports the `future` package (`pip install -r requirements.txt`).

There is no automated test suite yet: changes are verified manually against live trackers. Keep provider-specific logic inside `providers.json`; the Python modules must stay tracker-agnostic.

## Contributing

- **Broken provider**: open an issue with the tracker name, the search that failed and the relevant log lines.
- **New provider**: submit a pull request that adds the definition to `burst/providers/providers.json`, or publish it as a custom provider JSON.
- **Engine changes**: keep the payload and result format compatible with Jacktook.

## Credits

- [@elgatito](https://github.com/elgatito) for Elementum Burst, the base of this project.
- The Elementum Burst contributors who maintain the provider definitions upstream.

## Disclaimer

Jacktook Burst does not host, upload or distribute any content. It only queries publicly available torrent metadata and hands the links to Jacktook. The authors are not affiliated with any tracker.

## License

MIT — see [LICENSE](LICENSE).

Copyright (c) 2024 elgatito (original project)
Copyright (c) 2024-2026 sammax (fork modifications)

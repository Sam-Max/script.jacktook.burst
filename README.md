# Jacktook Burst

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A specialized torrent provider addon for [Jacktook](https://github.com/Sam-Max/plugin.video.jacktook) on Kodi.  
This is a fork of [Elementum Burst](https://github.com/elgatito/script.elementum.burst), adapted to work seamlessly with the Jacktook ecosystem.

## Overview

Jacktook Burst acts as a powerful "provider engine" for Jacktook. It searches a wide array of torrent sites (both public and private) to find streams for movies and TV shows. Instead of playing content directly, it gathers magnet links and torrent files and hands them off to Jacktook for processing and playback.

## Features

- **Multi-Provider Support**: Scrapes results from numerous popular torrent sites simultaneously.
- **Jacktook Integration**: Designed specifically to feed high-quality results into the Jacktook addon.
- **Customizable**: Easily enable or disable specific providers via the settings menu.
- **Extensible**: Supports custom provider definitions and overrides.
- **Fast**: Optimized for speed to get you results quickly.

## Installation

### Method 1: Jacktook Repository (Recommended)
1. Install the **Jacktook Repository** (if not already installed).
2. Go to **Add-ons** > **Install from repository** > **Jacktook Repository**.
3. Select **Program add-ons** > **Jacktook Burst**.
4. Click **Install**.

### Method 2: Manual Installation (Zip)
1. Download the latest release (`script.jacktook.burst-*.zip`) from the [Releases](https://github.com/Sam-Max/script.jacktook.burst/releases) page.
2. open Kodi and navigate to **Add-ons**.
3. Select **Install from zip file** (you may need to enable "Unknown sources" in System Settings).
4. Locate and select the downloaded zip file.

## Configuration

To configure Jacktook Burst:

1. Open Kodi and navigate to **Add-ons** > **Program add-ons**.
2. Right-click (or long-press/menu button) on **Jacktook Burst** and select **Settings**.
3. Configure available options:
    - **General**: adjust timeout settings and scraping behavior.
    - **Providers**: Toggle specific public and private trackers on or off. Note that private trackers often require account credentials.
    - **Filtering**: Set resolution preferences and keywords to include or exclude.

## Supported Providers

Jacktook Burst includes definitions for many popular trackers, including:

*   **Public**: 1337x, ThePirateBay, TorrentGalaxy, YTS, EZTV, MagnetDL, and many more.
*   **Private**: Supports various private trackers (credentials required in settings).

## Contributing

Contributions are welcome!
- **Bug Reports**: Open an issue if a provider is broken or site changes have occurred.
- **New Providers**: Submit a Pull Request with new provider definitions in `burst/providers/providers.json`.

## Credits

This project stands on the shoulders of giants. Huge thanks to:

- **[@elgatito](https://github.com/elgatito)** for Elementum Burst.
- **[@scakemyer](https://github.com/scakemyer)** for the original Quasar Burst module.
- **[@mancuniancol](https://github.com/mancuniancol)** for their extensive work on Magnetic.
- All the alpha and beta testers who contributed to the release.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

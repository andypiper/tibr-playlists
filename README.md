# The Indie Beat Radio Playlist Generator

A Python utility for generating playlist files for [The Indie Beat Radio](https://theindiebeat.fm) stations, so that they can easily be added to a range of media players.

## Overview

A Python utility for generating playlist files for The Indie Beat Radio stations. The scripts fetch station data from the AzuraCast API and create standardized playlist files that can be imported into media players.

## Scripts

- **get-playlists.py** - Main playlist generator with health checks and multiple format options
- **basic.py** - A simple utility to display station information in the terminal

## Features

- Generate playlists in multiple formats (XSPF, M3U, PLS)
- Perform health checks on streams before including them
- Display detailed information about available stations
- Command-line arguments for customization

## Requirements

- Python 3.11 or higher
- Dependencies:
  - requests
  - aiohttp
  - rich

## Installation

Clone this repository and install dependencies:

```bash
# With pip
pip install requests aiohttp rich

# With uv
uv pip install requests aiohttp rich

# Or use the script headers directly with uv
uv run get-playlists.py
```

## Usage

### Basic Station Information

```bash
python basic.py
```

### Generate Playlists

```bash
python get-playlists.py [options]
```

#### Options

- `-v, --verbose`: Enable verbose output
- `-o, --output FILENAME`: Set output filename (without extension)
- `-l, --list-streams`: List stream URLs without creating files
- `--xspf`: Generate XSPF playlist only
- `--m3u`: Generate M3U playlist only
- `--pls`: Generate PLS playlist only
- `--no-health-check`: Skip stream health checks

### Examples

```bash
# Generate all playlist formats with default filename
python get-playlists.py

# Generate only M3U format with verbose output
python get-playlists.py --m3u -v

# List all available streams
python get-playlists.py --list-streams

# Generate all formats with custom filename
python get-playlists.py -o tibr
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

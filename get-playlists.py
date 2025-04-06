#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "aiohttp",
#   "rich"
# ]
# ///
import requests
import asyncio
import aiohttp
import argparse
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime, UTC
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import os

console = Console()


class StreamHealthCheck:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.results = {}

    async def check_stream(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    # Read just the first chunk to verify stream is working
                    await response.content.read(1024)
                    return url, True, response.status
        except Exception as e:
            return url, False, str(e)

    async def check_streams(self, urls, verbose=False):
        if verbose:
            console.print("[bold blue]Starting health checks on streams...[/]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console if verbose else None,
            transient=True,
        ) as progress:
            task = progress.add_task(
                "[cyan]Checking streams...", total=len(urls))

            results = {}
            for url in urls:
                if verbose:
                    progress.update(task, description=f"[cyan]Checking: {url}")
                try:
                    result = await self.check_stream(url)
                    results[result[0]] = (result[1], result[2])
                except Exception as e:
                    results[url] = (False, str(e))
                progress.advance(task)

            return results


def fetch_station_data(verbose=False):
    # Use the /stations endpoint instead of /nowplaying for more concise data
    url = 'https://azura.theindiebeat.fm/api/stations'
    headers = {'accept': 'application/json'}

    if verbose:
        console.print(f"[bold blue]Fetching station data from:[/] {url}")

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    if verbose:
        console.print(
            f"[green]Successfully fetched data[/] (Status: {response.status_code})")

    return response.json()


def create_xspf_playlist(station_data, health_results):
    playlist = Element('playlist', version="1", xmlns="http://xspf.org/ns/0/")

    title = SubElement(playlist, 'title')
    title.text = "The Indie Beat Radio Streams"

    # Add creation date
    date = SubElement(playlist, 'date')
    date.text = datetime.now(UTC).isoformat()

    tracklist = SubElement(playlist, 'trackList')

    for station in station_data:
        for mount in station['mounts']:
            if mount['format'] == 'mp3':
                # Check if stream is healthy
                health_status = health_results.get(
                    mount['url'], (False, "Not checked"))[0]
                if not health_status:
                    continue

                track = SubElement(tracklist, 'track')

                location = SubElement(track, 'location')
                location.text = mount['url']

                title = SubElement(track, 'title')
                title.text = station['name']

                creator = SubElement(track, 'creator')
                creator.text = "The Indie Beat Radio"

                annotation = SubElement(track, 'annotation')
                annotation.text = station.get('description', '')

                info = SubElement(track, 'info')
                info.text = station.get('url', '')

                # Add genre information if available
                if 'genre' in station and station['genre']:
                    meta = SubElement(track, 'meta', attrib={'rel': 'genre'})
                    meta.text = station['genre']

                # Add artwork if available
                if 'art' in station and station['art']:
                    image = SubElement(track, 'image')
                    image.text = station['art']

    rough_string = tostring(playlist, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_m3u_playlist(station_data, health_results):
    m3u_content = "#EXTM3U\n"

    for station in station_data:
        for mount in station['mounts']:
            if mount['format'] == 'mp3':
                # Check if stream is healthy
                health_status = health_results.get(
                    mount['url'], (False, "Not checked"))[0]
                if not health_status:
                    continue

                # Add bitrate info if available
                bitrate_info = f" - {mount['bitrate']}kbps" if 'bitrate' in mount else ""

                m3u_content += f'#EXTINF:-1,{station["name"]}{bitrate_info}\n'
                m3u_content += f'{mount["url"]}\n'

    return m3u_content


def create_pls_playlist(station_data, health_results):
    pls_content = "[playlist]\n"
    valid_entries = 0

    for station in station_data:
        for mount in station['mounts']:
            if mount['format'] == 'mp3':
                # Check if stream is healthy
                health_status = health_results.get(
                    mount['url'], (False, "Not checked"))[0]
                if not health_status:
                    continue

                valid_entries += 1
                pls_content += f'File{valid_entries}={mount["url"]}\n'
                pls_content += f'Title{valid_entries}={station["name"]}\n'
                pls_content += f'Length{valid_entries}=-1\n'

    pls_content += f'NumberOfEntries={valid_entries}\n'
    pls_content += 'Version=2\n'

    return pls_content


def save_playlist(content, filename, verbose=False):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    if verbose:
        console.print(f"[green]✓ Saved playlist:[/] {filename}")


async def main():
    parser = argparse.ArgumentParser(
        description="Generate playlist files for The Indie Beat Radio streams",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')

    parser.add_argument('-o', '--output', type=str, default='the_indie_beat_radio',
                        help='Output filename (without extension)')

    parser.add_argument('-l', '--list-streams', action='store_true',
                        help='List stream URLs to console (no files created)')

    parser.add_argument('--xspf', action='store_true',
                        help='Generate XSPF playlist')
    parser.add_argument('--m3u', action='store_true',
                        help='Generate M3U playlist')
    parser.add_argument('--pls', action='store_true',
                        help='Generate PLS playlist')

    parser.add_argument('--no-health-check', action='store_true',
                        help='Skip network health checks')


    args = parser.parse_args()

    # default, enable all output formats
    if not any([args.xspf, args.m3u, args.pls]):
        args.xspf = args.m3u = args.pls = True

    try:
        # Fetch data from API
        if args.verbose:
            console.print("[bold]Fetching station data...[/]")
        station_data = fetch_station_data(args.verbose)

        # Get all MP3 stream URLs
        stream_urls = [
            mount['url']
            for station in station_data
            for mount in station['mounts']
            if mount['format'] == 'mp3'
        ]

        if args.list_streams:
            for url in stream_urls:
                    print(url)
            return 0

        # Perform health checks if enabled
        health_results = {}
        if not args.no_health_check:
            if not args.verbose:
                console.print(
                    "[bold]Performing health checks on streams...[/]")
            health_checker = StreamHealthCheck()
            health_results = await health_checker.check_streams(stream_urls, args.verbose)

            # Print health check results in a table
            table = Table(title="Stream Health Check Results")
            table.add_column("URL", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Details")

            for url, (status, info) in health_results.items():
                table.add_row(
                    url,
                    "[green]✓ OK[/]" if status else "[red]✗ Failed[/]",
                    str(info)
                )

            console.print(table)
        else:
            # Health check disabled
            health_results = {url: (True, "Health check skipped")
                              for url in stream_urls}
            if args.verbose:
                console.print("[yellow]Health checks skipped[/]")

        # Create and save playlists based on arguments
        if not args.verbose:
            console.print("[bold]Creating playlists...[/]")
        else:
            console.print("[bold blue]Creating playlists...[/]")

        output_files = []

        if args.xspf:
            xspf_filename = f"{args.output}.xspf"
            xspf_content = create_xspf_playlist(station_data, health_results)
            save_playlist(xspf_content, xspf_filename, args.verbose)
            output_files.append(xspf_filename)

        if args.m3u:
            m3u_filename = f"{args.output}.m3u"
            m3u_content = create_m3u_playlist(station_data, health_results)
            save_playlist(m3u_content, m3u_filename, args.verbose)
            output_files.append(m3u_filename)

        if args.pls:
            pls_filename = f"{args.output}.pls"
            pls_content = create_pls_playlist(station_data, health_results)
            save_playlist(pls_content, pls_filename, args.verbose)
            output_files.append(pls_filename)

        # Display summary
        if not args.verbose:
            console.print(
                f"[green]✓ Created {len(output_files)} playlist(s): {', '.join(output_files)}[/]")
        else:
            console.print(
                f"[bold green]Successfully created {len(output_files)} playlist(s)[/]")
            for file in output_files:
                console.print(f"  • {file} [{os.path.getsize(file)} bytes]")

    except requests.RequestException as e:
        console.print(f"[bold red]Error fetching data from API:[/] {e}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error creating playlists:[/] {e}")
        import traceback
        if args.verbose:
            console.print(traceback.format_exc())
        return 1

    return 0

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))

# /// script
# requires-python = ">=3.8"
# dependencies = ["requests", "rich"]
# ///

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from typing import Dict, Any, List, Optional

# Constants
API_BASE_URL = "https://azura.theindiebeat.fm/api"
USER_AGENT = "TheIndieBeat-ChannelLister/1.0"


def fetch_stations():
    """Fetch all stations from the AzuraCast API."""
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(f"{API_BASE_URL}/stations", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stations: {e}")
        return []


def fetch_now_playing(station_id):
    """Fetch current playing track information for a station."""
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            f"{API_BASE_URL}/nowplaying/{station_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching now playing for {station_id}: {e}")
        return None


def format_timestamp(timestamp: Optional[int]) -> str:
    """Format Unix timestamp to readable date or 'NULL' if None."""
    if not timestamp:
        return "NULL"
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "NULL"


def display_station_summary(stations: List[Dict[str, Any]]):
    """Display a summary table of all stations."""
    console = Console()

    table = Table(
        title=f"The Indie Beat Radio Channels - {len(stations)} found")

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Shortcode", style="yellow")
    table.add_column("Description", style="blue")
    table.add_column("Channel Art", style="magenta")
    table.add_column("Status", style="red")

    for station in stations:
        # Get the status for the station
        is_online = "ONLINE" if station.get("is_public", False) else "OFFLINE"

        # Check if channel art exists
        art_url = station.get("art", "NULL")
        art_status = "✅ Available" if art_url and art_url != "NULL" else "❌ Not Available"

        table.add_row(
            str(station.get("id", "NULL")),
            station.get("name", "NULL"),
            station.get("shortcode", "NULL"),
            station.get("description", "NULL") or "NULL",
            art_status,
            is_online
        )

    console.print(table)


def display_stations_detailed(stations: List[Dict[str, Any]]):
    """Display detailed information about each station."""
    console = Console()

    console.print(Panel(
        f"[bold blue]The Indie Beat Radio Channels[/bold blue] - {len(stations)} channels found", expand=False))

    for idx, station in enumerate(stations):
        # Fetch now playing information for more metadata
        now_playing = fetch_now_playing(station.get("shortcode", ""))

        # Create a panel for each station
        station_info = [
            f"[bold cyan]Channel #{idx+1}[/bold cyan]",
            f"[bold]ID:[/bold] {station.get('id', 'NULL')}",
            f"[bold]Name:[/bold] {station.get('name', 'NULL')}",
            f"[bold]Shortcode:[/bold] {station.get('shortcode', 'NULL')}",
            f"[bold]Description:[/bold] {station.get('description', 'NULL') or 'NULL'}",
            f"[bold]Genre:[/bold] {station.get('genre', 'NULL') or 'NULL'}",
            f"[bold]URL:[/bold] {station.get('url', 'NULL') or 'NULL'}",

            # Station broadcasting details
            f"[bold]Frontend:[/bold] {station.get('frontend', 'NULL') or 'NULL'}",
            f"[bold]Backend:[/bold] {station.get('backend', 'NULL') or 'NULL'}",
            f"[bold]Listen URL:[/bold] {station.get('listen_url', 'NULL') or 'NULL'}",
            f"[bold]Public Player URL:[/bold] {station.get('public_player_url', 'NULL') or 'NULL'}",
            f"[bold]Playlist URL (PLS):[/bold] {station.get('playlist_pls_url', 'NULL') or 'NULL'}",
            f"[bold]Playlist URL (M3U):[/bold] {station.get('playlist_m3u_url', 'NULL') or 'NULL'}",

            # Channel art (station art)
            f"[bold]Channel Art URL:[/bold] {station.get('art', 'NULL') or 'NULL'}",

            # Status info
            f"[bold]Is Public:[/bold] {str(station.get('is_public', 'NULL'))}",
            f"[bold]Timezone:[/bold] {station.get('timezone', 'NULL') or 'NULL'}",
        ]

        # Mount points information
        mounts = station.get('mounts', [])
        if mounts:
            station_info.append(
                f"\n[bold magenta]MOUNT POINTS ({len(mounts)}):[/bold magenta]")
            for i, mount in enumerate(mounts):
                station_info.extend([
                    f"  [bold]Mount #{i+1}:[/bold] {mount.get('name', 'NULL')}",
                    f"  [bold]URL:[/bold] {mount.get('url', 'NULL')}",
                    f"  [bold]Bitrate:[/bold] {mount.get('bitrate', 'NULL') or 'NULL'} kbps",
                    f"  [bold]Format:[/bold] {mount.get('format', 'NULL') or 'NULL'}",
                    f"  [bold]Is Default:[/bold] {str(mount.get('is_default', False))}",
                    ""
                ])

        # HLS streaming info
        if station.get('hls_enabled', False):
            station_info.extend([
                f"\n[bold yellow]HLS STREAMING:[/bold yellow]",
                f"  [bold]HLS Enabled:[/bold] {str(station.get('hls_enabled', False))}",
                f"  [bold]HLS Is Default:[/bold] {str(station.get('hls_is_default', False))}",
                f"  [bold]HLS URL:[/bold] {station.get('hls_url', 'NULL') or 'NULL'}",
                f"  [bold]HLS Listeners:[/bold] {station.get('hls_listeners', 0)}"
            ])

        # Add now playing information if available
        if now_playing:
            station_info.append("\n[bold green]NOW PLAYING:[/bold green]")

            np = now_playing.get("now_playing", {})
            song = np.get("song", {}) if np else {}

            if song:
                station_info.extend([
                    f"  [bold]Title:[/bold] {song.get('title', 'NULL') or 'NULL'}",
                    f"  [bold]Artist:[/bold] {song.get('artist', 'NULL') or 'NULL'}",
                    f"  [bold]Album:[/bold] {song.get('album', 'NULL') or 'NULL'}",
                    f"  [bold]Album Art URL:[/bold] {song.get('art', 'NULL') or 'NULL'}"
                ])

                # Add any custom fields if available
                custom_fields = song.get("custom_fields", {})
                if custom_fields:
                    station_info.append(
                        "\n  [bold yellow]CUSTOM FIELDS:[/bold yellow]")
                    for key, value in custom_fields.items():
                        station_info.append(
                            f"    [bold]{key}:[/bold] {value if value else 'NULL'}")

            # Add listener info
            listeners = now_playing.get("listeners", {})
            if listeners:
                station_info.extend([
                    f"\n  [bold]Current Listeners:[/bold] {listeners.get('current', 0)}",
                    f"  [bold]Unique Listeners:[/bold] {listeners.get('unique', 0)}"
                ])

        # Display station panel
        console.print(Panel("\n".join(station_info), title=station.get("name", f"Channel {idx+1}"),
                            border_style="green"))

        if idx < len(stations) - 1:
            console.print()  # Add space between stations


def main():
    console = Console()
    console.print("[bold]Fetching The Indie Beat radio channels...[/bold]")
    stations = fetch_stations()

    if stations:
        # Show options to the user
        console.print("\n[yellow]Choose a display option:[/yellow]")
        console.print("[1] Summary view (basic information for all stations)")
        console.print(
            "[2] Detailed view (complete information for each station)\n")

        choice = input("Enter your choice (1 or 2): ")

        if choice == "1":
            display_station_summary(stations)
        else:
            display_stations_detailed(stations)
    else:
        console.print(
            "[bold red]No stations found or there was an error fetching the data.[/bold red]")


if __name__ == "__main__":
    main()

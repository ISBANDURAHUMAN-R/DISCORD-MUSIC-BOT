"""Void Vibe — Discord Embed Presentation Layer.

🎧 Your soundtrack, your server.
Play music, manage queues, and enjoy your favorite tracks with Void Vibe.
Implements the sleek, dark obsidian and neon purple Void Vibe theme,
dynamic progress bars, source badges, and standardized feedback embeds.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

import discord
import wavelink

# ==============================================================================
# VOID VIBE COLOR PALETTE (Dark Obsidian & Deep Neon Purple)
# ==============================================================================
COLOR_VOID_VIBE_PRIMARY = 0x7B2CBF  # Deep Neon Purple
COLOR_VOID_VIBE_DARK = 0x1A0B2E     # Deep Obsidian Black/Purple
COLOR_VOID_VIBE_SUCCESS = 0x10B981  # Emerald Accent
COLOR_VOID_VIBE_ERROR = 0xEF4444    # Crimson Accent
COLOR_VOID_VIBE_WARNING = 0xF59E0B  # Amber Accent
COLOR_VOID_VIBE_INFO = 0x3B82F6     # Sapphire Accent

# Backwards compatibility color aliases
COLOR_VOIDKAGE_PRIMARY = COLOR_VOID_VIBE_PRIMARY
COLOR_VOIDKAGE_DARK = COLOR_VOID_VIBE_DARK
COLOR_VOIDKAGE_SUCCESS = COLOR_VOID_VIBE_SUCCESS
COLOR_VOIDKAGE_ERROR = COLOR_VOID_VIBE_ERROR
COLOR_VOIDKAGE_WARNING = COLOR_VOID_VIBE_WARNING
COLOR_VOIDKAGE_INFO = COLOR_VOID_VIBE_INFO

VOID_VIBE_FOOTER_ICON = None  # None prevents Discord from displaying a broken/expired image icon
VOIDKAGE_FOOTER_ICON = None
DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&q=80"
VOID_VIBE_TAGLINE = "🎧 Your soundtrack, your server."


def format_duration(ms: int) -> str:
    """Format milliseconds into a human-readable mm:ss or hh:mm:ss string."""
    if ms is None or ms <= 0:
        return "00:00"

    total_seconds = int(ms // 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def render_progress_bar(current_ms: int, total_ms: int, bar_length: int = 14) -> str:
    """Render a modern visual progress bar with an indicator node."""
    if total_ms <= 0:
        return f"`LIVE` [{'🔘' + '▬' * (bar_length - 1)}]"

    ratio = min(max(current_ms / total_ms, 0.0), 1.0)
    progress_chars = int(ratio * bar_length)

    before_node = "▬" * progress_chars
    after_node = "▬" * (bar_length - progress_chars)
    bar = f"{before_node}🔘{after_node}"

    cur_str = format_duration(current_ms)
    tot_str = format_duration(total_ms)
    return f"`{cur_str}` [{bar}] `{tot_str}`"


def get_source_label(track: wavelink.Playable) -> str:
    """Determine friendly display badge for the music source."""
    source_name = getattr(track, "source", "") or ""
    source_name = str(source_name).lower()

    if "soundcloud" in source_name:
        return "🟧 SoundCloud"
    elif "spotify" in source_name:
        return "🟩 Spotify"
    elif "apple" in source_name:
        return "🍎 Apple Music"
    elif "bandcamp" in source_name:
        return "🟦 Bandcamp"
    elif "twitch" in source_name:
        return "🟪 Twitch"
    elif "youtube" in source_name:
        return "🟥 YouTube"
    elif "http" in source_name:
        return "🌐 Direct Stream"
    return "🎵 Audio Stream"


def get_requester_mention(track: wavelink.Playable) -> str:
    """Extract requester mention or name from track extras."""
    extras = getattr(track, "extras", None)
    if extras:
        # Check dict access or attribute access
        req_id = getattr(extras, "requester_id", None)
        req_name = getattr(extras, "requester_name", None)
        if not req_id and isinstance(extras, dict):
            req_id = extras.get("requester_id")
            req_name = extras.get("requester_name")
        if req_id:
            return f"<@{req_id}>"
        if req_name:
            return f"**{req_name}**"
    return "Unknown Requester"


def now_playing_embed(player: wavelink.Player, track: wavelink.Playable) -> discord.Embed:
    """Construct the Void Vibe now playing display embed."""
    embed = discord.Embed(
        title="🎧 VOID VIBE — NOW PLAYING",
        color=COLOR_VOID_VIBE_PRIMARY,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    track_title = track.title or "Unknown Title"
    track_uri = track.uri or "https://discord.com"
    embed.description = f"### [{track_title}]({track_uri})\n"

    # Artist and Source
    artist = track.author or "Unknown Artist"
    source = get_source_label(track)
    requester = get_requester_mention(track)

    embed.add_field(name="🎙️ Artist", value=f"`{artist}`", inline=True)
    embed.add_field(name="📡 Source", value=f"`{source}`", inline=True)
    embed.add_field(name="👤 Requester", value=requester, inline=True)

    # Playback Progress
    if track.is_stream:
        progress_str = "🔴 **LIVE STREAM** — Non-seekable direct broadcast"
    else:
        position = player.position or 0
        progress_str = render_progress_bar(position, track.length)

    embed.add_field(name="⏳ Progress", value=progress_str, inline=False)

    # State indicators: Status, Loop, Volume, Queue Size
    status_icon = "⏸️ Paused" if player.paused else "▶️ Playing"

    mode = player.queue.mode
    loop_str = "Off"
    if mode == wavelink.QueueMode.loop:
        loop_str = "🔂 Track Loop"
    elif mode == wavelink.QueueMode.loop_all:
        loop_str = "🔁 Queue Loop"

    volume_str = f"🔊 {player.volume}%"
    queue_len = len(player.queue)

    embed.add_field(
        name="🎛️ Player State",
        value=(
            f"**Status:** {status_icon} | "
            f"**Loop:** `{loop_str}` | "
            f"**Volume:** `{volume_str}` | "
            f"**Queue:** `{queue_len} upcoming`"
        ),
        inline=False,
    )

    # Artwork
    artwork = getattr(track, "artwork", None)
    if artwork:
        embed.set_thumbnail(url=artwork)

    embed.set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)
    return embed


def track_queued_embed(
    track: wavelink.Playable, position: int, queue_duration_ms: int
) -> discord.Embed:
    """Embed confirming a track has been appended to the server queue."""
    embed = discord.Embed(
        title="📥 Added to Queue",
        description=f"**[{track.title}]({track.uri or 'https://discord.com'})**",
        color=COLOR_VOID_VIBE_PRIMARY,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    embed.add_field(name="🎙️ Artist", value=f"`{track.author or 'Unknown'}`", inline=True)
    embed.add_field(
        name="⏱️ Duration",
        value=f"`{format_duration(track.length) if not track.is_stream else 'LIVE'}`",
        inline=True,
    )
    embed.add_field(name="🔢 Position in Queue", value=f"`#{position}`", inline=True)

    time_until = format_duration(queue_duration_ms) if queue_duration_ms > 0 else "Playing Next"
    embed.add_field(name="⌛ Estimated Play Time", value=f"`{time_until}`", inline=True)
    embed.add_field(name="👤 Requester", value=get_requester_mention(track), inline=True)

    if track.artwork:
        embed.set_thumbnail(url=track.artwork)

    embed.set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)
    return embed


def playlist_queued_embed(
    name: str, count: int, total_ms: int, requester_mention: str, artwork: Optional[str] = None
) -> discord.Embed:
    """Embed confirming a playlist has been enqueued."""
    embed = discord.Embed(
        title="📚 Enqueued Playlist",
        description=f"### **{name}**",
        color=COLOR_VOID_VIBE_PRIMARY,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    embed.add_field(name="🎵 Tracks Added", value=f"`{count} songs`", inline=True)
    embed.add_field(name="⏱️ Total Duration", value=f"`{format_duration(total_ms)}`", inline=True)
    embed.add_field(name="👤 Requester", value=requester_mention, inline=True)

    if artwork:
        embed.set_thumbnail(url=artwork)

    embed.set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)
    return embed


def queue_embed(player: wavelink.Player, page: int = 1, per_page: int = 10) -> discord.Embed:
    """Paginated embed showing current track and upcoming queue."""
    total_tracks = len(player.queue)
    total_pages = max((total_tracks + per_page - 1) // per_page, 1)
    page = max(min(page, total_pages), 1)

    embed = discord.Embed(
        title="🎵 VOID VIBE — MUSIC QUEUE",
        color=COLOR_VOID_VIBE_PRIMARY,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    # Current Track Header
    current = player.current
    if current:
        cur_duration = format_duration(current.length) if not current.is_stream else "LIVE"
        embed.description = (
            f"**Now Playing:**\n"
            f"▶ [{current.title}]({current.uri or 'https://discord.com'}) "
            f"(`{cur_duration}`) — {get_requester_mention(current)}\n\n"
            f"**Up Next ({total_tracks}):**\n"
        )
    else:
        embed.description = "**Nothing currently playing.**\n\n**Up Next:**\n"

    if total_tracks == 0:
        embed.description += "*The queue is currently empty. Add tracks with `/play <query>`!*"
    else:
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_tracks)

        # Slice queue
        tracks_slice = list(player.queue)[start_idx:end_idx]
        lines = []
        for i, trk in enumerate(tracks_slice, start=start_idx + 1):
            dur = format_duration(trk.length) if not trk.is_stream else "LIVE"
            req = get_requester_mention(trk)
            lines.append(f"`{i}.` [{trk.title}]({trk.uri or 'https://discord.com'}) (`{dur}`) | {req}")

        embed.description += "\n".join(lines)

    # Total remaining duration
    total_remaining_ms = sum(t.length for t in player.queue if not t.is_stream)
    if current and not current.is_stream:
        total_remaining_ms += max(0, current.length - (player.position or 0))

    mode_text = "Off"
    if player.queue.mode == wavelink.QueueMode.loop:
        mode_text = "🔂 Track Loop"
    elif player.queue.mode == wavelink.QueueMode.loop_all:
        mode_text = "🔁 Queue Loop"

    embed.add_field(
        name="📊 Queue Stats",
        value=(
            f"**Total Songs:** `{total_tracks}` | "
            f"**Total Remaining:** `{format_duration(total_remaining_ms)}` | "
            f"**Loop Mode:** `{mode_text}`"
        ),
        inline=False,
    )

    embed.set_footer(
        text=f"Page {page} of {total_pages} • Void Vibe",
        icon_url=VOID_VIBE_FOOTER_ICON,
    )
    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    """Clean success embed with emerald accent."""
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=COLOR_VOID_VIBE_SUCCESS,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    ).set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)


def error_embed(title: str, description: str) -> discord.Embed:
    """Clean error embed with crimson accent."""
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=COLOR_VOID_VIBE_ERROR,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    ).set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)


def warning_embed(title: str, description: str) -> discord.Embed:
    """Clean warning embed with amber accent."""
    return discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=COLOR_VOID_VIBE_WARNING,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    ).set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)


def info_embed(title: str, description: str) -> discord.Embed:
    """Clean info embed with sapphire accent."""
    return discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=COLOR_VOID_VIBE_INFO,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    ).set_footer(text=f"Void Vibe • {VOID_VIBE_TAGLINE}", icon_url=VOID_VIBE_FOOTER_ICON)


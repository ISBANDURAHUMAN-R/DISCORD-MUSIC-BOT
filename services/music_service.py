"""Void Vibe — Music Source Resolution Service.

🎧 Your soundtrack, your server.
Play music, manage queues, and enjoy your favorite tracks with Void Vibe.
Abstracts audio provider searching, URL dispatching, playlist handling,
and requester metadata injection.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union
from urllib.parse import urlparse

import discord
import wavelink

if TYPE_CHECKING:
    from wavelink import Playable, Playlist

logger = logging.getLogger("voidvibe.music_service")

# Regex pattern for general web URLs
URL_REGEX = re.compile(
    r"^https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)$"
)


class MusicServiceError(Exception):
    """Base exception for music service operations."""


class NoTracksFoundError(MusicServiceError):
    """Raised when a search query or URL returns zero playable tracks."""


class SourceUnavailableError(MusicServiceError):
    """Raised when an external music provider is unreachable or returns an error."""


@dataclass
class SearchResult:
    """Standardized representation of query search results."""

    tracks: List[Playable]
    playlist: Optional[Playlist] = None
    is_playlist: bool = False
    source_description: str = "Search Query"


class MusicService:
    """Service for resolving music tracks from multiple providers."""

    # Default search provider for text queries: YouTube (backed by dev.lavalink.youtube plugin)
    DEFAULT_SOURCE = wavelink.TrackSource.YouTube
    FALLBACK_SOURCE = wavelink.TrackSource.YouTubeMusic

    @classmethod
    def is_url(cls, query: str) -> bool:
        """Check if the provided query is a valid HTTP/HTTPS URL."""
        return bool(URL_REGEX.match(query.strip()))

    @classmethod
    def identify_url_provider(cls, url: str) -> str:
        """Identify which music platform a URL points to."""
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if "soundcloud.com" in netloc or "snd.sc" in netloc:
            return "SoundCloud"
        elif "spotify.com" in netloc:
            return "Spotify"
        elif "apple.com" in netloc:
            return "Apple Music"
        elif "bandcamp.com" in netloc:
            return "Bandcamp"
        elif "twitch.tv" in netloc:
            return "Twitch"
        elif "youtube.com" in netloc or "youtu.be" in netloc:
            return "YouTube"
        return "Direct Audio Link"

    @classmethod
    async def search(
        cls,
        query: str,
        requester: discord.Member,
        preferred_source: Optional[Union[wavelink.TrackSource, str]] = None,
    ) -> SearchResult:
        """Search for tracks or resolve a URL using configured Lavalink sources.

        Args:
            query: The search keywords or URL.
            requester: The Discord member who initiated the request.
            preferred_source: Optional provider override for text searches.

        Returns:
            SearchResult containing list of playable tracks and metadata.

        Raises:
            NoTracksFoundError: If no tracks match.
            SourceUnavailableError: If Lavalink or source fails, explaining the specific cause.
        """
        clean_query = query.strip()
        is_query_url = cls.is_url(clean_query)

        user_extras = {
            "requester_id": requester.id,
            "requester_name": requester.display_name,
            "requester_avatar": requester.display_avatar.url if requester.display_avatar else None,
        }

        # ----------------------------------------------------------------------
        # Case A: URL Resolution
        # ----------------------------------------------------------------------
        if is_query_url:
            provider_name = cls.identify_url_provider(clean_query)
            logger.info("Resolving %s URL: %s", provider_name, clean_query)
            try:
                tracks: Union[List[Playable], Playlist] = await wavelink.Playable.search(clean_query)
                source_desc = f"{provider_name} URL"
            except wavelink.LavalinkLoadException as exc:
                logger.error("Lavalink failed to load %s URL '%s': %s", provider_name, clean_query, exc)
                if provider_name == "Spotify":
                    raise SourceUnavailableError(
                        "**Spotify resolution failed.**\n"
                        "Spotify link resolution requires configured API credentials "
                        "(`SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`) in `.env` and `application.yml`.\n\n"
                        "💡 **Tip:** You can play this song immediately by searching its title: `/play <song title or artist>`"
                    ) from exc
                elif provider_name == "Apple Music":
                    raise SourceUnavailableError(
                        "**Apple Music resolution failed.**\n"
                        "Apple Music is currently disabled and requires an Apple Developer Media API token.\n\n"
                        "💡 **Tip:** You can play this song immediately by searching its title: `/play <song title or artist>`"
                    ) from exc
                elif provider_name == "SoundCloud":
                    raise SourceUnavailableError(
                        "**SoundCloud resolution failed.**\n"
                        "SoundCloud did not return any supported audio formats for this track. "
                        "The stream may be geo-restricted, private, or SoundCloud format layouts may have changed.\n\n"
                        "💡 **Tip:** Try searching for the song title directly: `/play <song title>`"
                    ) from exc
                elif provider_name == "YouTube":
                    raise SourceUnavailableError(
                        "**YouTube resolution failed.**\n"
                        "The video or playlist may be private, age-restricted, region-blocked, or unavailable."
                    ) from exc
                else:
                    raise SourceUnavailableError(
                        f"**{provider_name} resolution failed.**\n"
                        f"Unable to load audio stream from this link ({exc})."
                    ) from exc
            except Exception as exc:
                logger.error("Unexpected error loading URL '%s': %s", clean_query, exc, exc_info=True)
                raise SourceUnavailableError(
                    f"**Failed to resolve {provider_name} link.** An unexpected communication error occurred: {exc}"
                ) from exc

        # ----------------------------------------------------------------------
        # Case B: Text Keyword Search
        # ----------------------------------------------------------------------
        else:
            primary_source = preferred_source or cls.DEFAULT_SOURCE
            source_name = getattr(primary_source, "name", str(primary_source))
            logger.info("Searching via %s: '%s'", source_name, clean_query)

            tracks = None
            primary_error: Optional[Exception] = None

            try:
                tracks = await wavelink.Playable.search(clean_query, source=primary_source)
                source_desc = f"{source_name} Search"
            except wavelink.LavalinkLoadException as exc:
                primary_error = exc
                logger.warning("Primary search via %s failed for '%s': %s", source_name, clean_query, exc)
            except Exception as exc:
                primary_error = exc
                logger.warning("Primary search via %s encountered unexpected error for '%s': %s", source_name, clean_query, exc)

            # Automatic Fallback: If primary search failed or returned 0 tracks, and preferred_source was not explicitly overridden
            if (not tracks or primary_error) and not preferred_source and primary_source != cls.FALLBACK_SOURCE:
                fallback_name = getattr(cls.FALLBACK_SOURCE, "name", str(cls.FALLBACK_SOURCE))
                logger.info("Attempting automatic fallback search via %s for: '%s'", fallback_name, clean_query)
                try:
                    tracks = await wavelink.Playable.search(clean_query, source=cls.FALLBACK_SOURCE)
                    if tracks:
                        source_desc = f"{fallback_name} Search"
                        primary_error = None  # Cleared by successful fallback
                except Exception as fb_exc:
                    logger.error("Fallback search via %s also failed for '%s': %s", fallback_name, clean_query, fb_exc)

            if not tracks:
                if primary_error:
                    err_text = str(primary_error)
                    if "Did not detect any supported formats" in err_text:
                        fail_reason = f"**{source_name} Search Failed:** SoundCloud did not detect any supported audio formats."
                    else:
                        fail_reason = f"**{source_name} Search Failed:** {err_text}"
                    raise SourceUnavailableError(
                        f"{fail_reason}\n\n"
                        "💡 **Tip:** Try using different keywords, adding the artist name, or providing a direct YouTube URL."
                    ) from primary_error

                raise NoTracksFoundError(
                    f"No playable tracks were found matching: `{clean_query}`.\n\n"
                    "💡 **Tip:** Try using specific keywords (e.g. `Song Title Artist`) or a direct YouTube URL."
                )

        # ----------------------------------------------------------------------
        # Process Results (Playlist vs Single Track)
        # ----------------------------------------------------------------------
        if isinstance(tracks, wavelink.Playlist):
            tracks.extras = user_extras
            playlist_tracks = list(tracks.tracks)
            if not playlist_tracks:
                raise NoTracksFoundError("The requested playlist appears to be empty or private.")
            return SearchResult(
                tracks=playlist_tracks,
                playlist=tracks,
                is_playlist=True,
                source_description=f"Playlist ({len(playlist_tracks)} tracks)",
            )

        playable_list: List[Playable] = list(tracks)
        for trk in playable_list:
            trk.extras = user_extras

        return SearchResult(
            tracks=playable_list,
            playlist=None,
            is_playlist=False,
            source_description=source_desc,
        )

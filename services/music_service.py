"""VOIDKAGE MUSIC - Music Source Resolution Service.

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

logger = logging.getLogger("voidkage.music_service")

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

    # Default search provider for text queries: TrackSource.SoundCloud or YouTubeMusic
    # SoundCloud is natively enabled in Lavalink v4 without requiring YouTube oauth
    DEFAULT_SOURCE = wavelink.TrackSource.SoundCloud

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
            SourceUnavailableError: If Lavalink or source fails.
        """
        clean_query = query.strip()
        is_query_url = cls.is_url(clean_query)

        user_extras = {
            "requester_id": requester.id,
            "requester_name": requester.display_name,
            "requester_avatar": requester.display_avatar.url if requester.display_avatar else None,
        }

        try:
            if is_query_url:
                provider_name = cls.identify_url_provider(clean_query)
                logger.debug("Resolving URL (%s): %s", provider_name, clean_query)
                tracks: Union[List[Playable], Playlist] = await wavelink.Playable.search(clean_query)
                source_desc = f"{provider_name} URL"
            else:
                source = preferred_source or cls.DEFAULT_SOURCE
                source_name = getattr(source, "name", str(source))
                logger.debug("Searching via %s: %s", source_name, clean_query)
                tracks = await wavelink.Playable.search(clean_query, source=source)
                source_desc = f"{source_name} Search"

        except wavelink.LavalinkLoadException as exc:
            provider_hint = cls.identify_url_provider(clean_query) if is_query_url else "configured source"
            logger.error("Lavalink failed to load query '%s': %s", clean_query, exc)
            raise SourceUnavailableError(
                f"The audio provider ({provider_hint}) was unable to load this track. "
                "The track may be region-restricted, private, or requires authentication."
            ) from exc

        except Exception as exc:
            logger.error("Unexpected error searching for '%s': %s", clean_query, exc, exc_info=True)
            raise SourceUnavailableError(
                "An unexpected error occurred while communicating with the music audio node. "
                "Please verify Lavalink status or try a different search query."
            ) from exc

        if not tracks:
            raise NoTracksFoundError(
                f"No playable tracks were found matching: `{clean_query}`.\n"
                "Tip: Try using specific keywords (e.g. `Song Title Artist`) or a direct SoundCloud/YouTube URL."
            )

        # Handle Playlist
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

        # Handle single track or list of search results
        playable_list: List[Playable] = list(tracks)
        for trk in playable_list:
            trk.extras = user_extras

        return SearchResult(
            tracks=playable_list,
            playlist=None,
            is_playlist=False,
            source_description=source_desc,
        )

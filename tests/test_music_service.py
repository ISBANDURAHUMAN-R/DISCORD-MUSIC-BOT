"""Unit tests for MusicService provider detection, error handling, and search routing."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import wavelink

from services.music_service import (
    MusicService,
    MusicServiceError,
    NoTracksFoundError,
    SourceUnavailableError,
    SearchResult,
)


class TestMusicServiceUrlAndSourceDetection:
    """Tests for URL detection and provider classification."""

    def test_is_url(self):
        assert MusicService.is_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert MusicService.is_url("http://soundcloud.com/artist/track") is True
        assert MusicService.is_url("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT") is True
        assert MusicService.is_url("alan walker faded") is False
        assert MusicService.is_url("scsearch:faded") is False
        assert MusicService.is_url("ytsearch:faded") is False

    def test_identify_url_provider(self):
        assert MusicService.identify_url_provider("https://soundcloud.com/artist/track") == "SoundCloud"
        assert MusicService.identify_url_provider("https://snd.sc/abc1234") == "SoundCloud"
        assert MusicService.identify_url_provider("https://open.spotify.com/track/xyz") == "Spotify"
        assert MusicService.identify_url_provider("https://music.apple.com/us/album/xyz") == "Apple Music"
        assert MusicService.identify_url_provider("https://artist.bandcamp.com/track/song") == "Bandcamp"
        assert MusicService.identify_url_provider("https://twitch.tv/streamer") == "Twitch"
        assert MusicService.identify_url_provider("https://www.youtube.com/watch?v=123") == "YouTube"
        assert MusicService.identify_url_provider("https://youtu.be/123") == "YouTube"
        assert MusicService.identify_url_provider("https://example.com/audio.mp3") == "Direct Audio Link"

    def test_default_sources(self):
        assert MusicService.DEFAULT_SOURCE == wavelink.TrackSource.YouTube
        assert MusicService.FALLBACK_SOURCE == wavelink.TrackSource.YouTubeMusic


class TestMusicServiceExceptions:
    """Tests for error hierarchy and informative error messaging."""

    def test_exception_hierarchy(self):
        assert issubclass(NoTracksFoundError, MusicServiceError)
        assert issubclass(SourceUnavailableError, MusicServiceError)

    @pytest.mark.asyncio
    async def test_spotify_url_explains_missing_credentials(self):
        mock_requester = MagicMock()
        mock_requester.id = 123
        mock_requester.display_name = "User"
        mock_requester.display_avatar.url = "http://avatar.png"

        err_payload = {"message": "403 Forbidden", "severity": "FAULT", "cause": "Missing token"}
        with patch("wavelink.Playable.search", side_effect=wavelink.LavalinkLoadException(data=err_payload)):
            with pytest.raises(SourceUnavailableError) as exc_info:
                await MusicService.search("https://open.spotify.com/track/xyz", requester=mock_requester)

            err_msg = str(exc_info.value)
            assert "Spotify resolution failed" in err_msg
            assert "SPOTIFY_CLIENT_ID" in err_msg
            assert "/play <song title" in err_msg

    @pytest.mark.asyncio
    async def test_soundcloud_url_explains_unsupported_formats(self):
        mock_requester = MagicMock()
        mock_requester.id = 123
        mock_requester.display_name = "User"
        mock_requester.display_avatar.url = "http://avatar.png"

        err_payload = {
            "message": "Did not detect any supported formats",
            "severity": "COMMON",
            "cause": "Format layout changed",
        }
        with patch("wavelink.Playable.search", side_effect=wavelink.LavalinkLoadException(data=err_payload)):
            with pytest.raises(SourceUnavailableError) as exc_info:
                await MusicService.search("https://soundcloud.com/artist/track", requester=mock_requester)

            err_msg = str(exc_info.value)
            assert "SoundCloud resolution failed" in err_msg
            assert "supported audio formats" in err_msg

    @pytest.mark.asyncio
    async def test_text_search_fallback_to_youtubemusic(self):
        mock_requester = MagicMock()
        mock_requester.id = 123
        mock_requester.display_name = "User"
        mock_requester.display_avatar.url = "http://avatar.png"

        mock_fallback_track = MagicMock(spec=wavelink.Playable)
        mock_fallback_track.title = "Faded (Audio)"
        mock_fallback_track.length = 200000
        mock_fallback_track.is_stream = False

        err_payload = {"message": "Quota exceeded", "severity": "COMMON", "cause": "Rate limit"}
        # First call (YouTube) fails, second call (YouTubeMusic) succeeds
        with patch("wavelink.Playable.search", side_effect=[wavelink.LavalinkLoadException(data=err_payload), [mock_fallback_track]]):
            result = await MusicService.search("faded", requester=mock_requester)

            assert isinstance(result, SearchResult)
            assert len(result.tracks) == 1
            assert result.tracks[0] == mock_fallback_track
            assert "YouTubeMusic" in result.source_description

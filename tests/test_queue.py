"""Unit tests for VOIDKAGE MUSIC QueueService, looping modes, and UI formatters."""

from unittest.mock import MagicMock
import pytest
import wavelink

from services.queue_service import LoopMode, QueueService
from utils.embeds import format_duration, render_progress_bar
from utils.validators import InputValidationError


def create_mock_track(title: str, length_ms: int = 180000, is_stream: bool = False) -> wavelink.Playable:
    """Create a mock track matching wavelink.Playable specification."""
    track = MagicMock(spec=wavelink.Playable)
    track.title = title
    track.author = "Test Artist"
    track.uri = f"https://example.com/{title.replace(' ', '_')}"
    track.length = length_ms
    track.is_stream = is_stream
    track.artwork = None
    track.extras = {"requester_name": "TestUser"}
    return track


class TestQueueService:
    """Test suite for QueueService operations."""

    @pytest.fixture
    def mock_player(self):
        """Create a mock Wavelink player equipped with a real Wavelink Queue."""
        player = MagicMock(spec=wavelink.Player)
        player.queue = wavelink.Queue()
        player.current = None
        player.position = 0
        return player

    def test_loop_mode_transitions(self, mock_player):
        # 1. Normal / Off
        mode, desc = QueueService.set_loop_mode(mock_player, "off")
        assert mode == wavelink.QueueMode.normal
        assert mock_player.queue.mode == wavelink.QueueMode.normal
        assert "disabled" in desc.lower()

        # 2. Track Loop
        mode, desc = QueueService.set_loop_mode(mock_player, "track")
        assert mode == wavelink.QueueMode.loop
        assert mock_player.queue.mode == wavelink.QueueMode.loop
        assert "track loop" in desc.lower()

        # 3. Queue Loop
        mode, desc = QueueService.set_loop_mode(mock_player, "queue")
        assert mode == wavelink.QueueMode.loop_all
        assert mock_player.queue.mode == wavelink.QueueMode.loop_all
        assert "queue loop" in desc.lower()

        # 4. Enum input
        mode, desc = QueueService.set_loop_mode(mock_player, LoopMode.TRACK)
        assert mode == wavelink.QueueMode.loop

        # 5. Invalid mode
        with pytest.raises(InputValidationError, match="Unknown loop mode"):
            QueueService.set_loop_mode(mock_player, "invalid_loop_mode")

    def test_remove_at_valid(self, mock_player):
        t1 = create_mock_track("Track 1")
        t2 = create_mock_track("Track 2")
        t3 = create_mock_track("Track 3")
        mock_player.queue.put([t1, t2, t3])

        # Remove track at position 2 (1-based: Track 2)
        removed = QueueService.remove_at(mock_player, 2)
        assert removed == t2
        assert len(mock_player.queue) == 2
        assert mock_player.queue[0] == t1
        assert mock_player.queue[1] == t3

    def test_remove_at_out_of_bounds(self, mock_player):
        t1 = create_mock_track("Track 1")
        mock_player.queue.put(t1)

        with pytest.raises(InputValidationError, match="Invalid queue position"):
            QueueService.remove_at(mock_player, 2)

        with pytest.raises(InputValidationError, match="Invalid queue position"):
            QueueService.remove_at(mock_player, 0)

    def test_clear_queue(self, mock_player):
        tracks = [create_mock_track(f"Track {i}") for i in range(5)]
        mock_player.queue.put(tracks)
        assert len(mock_player.queue) == 5

        cleared_count = QueueService.clear_queue(mock_player)
        assert cleared_count == 5
        assert len(mock_player.queue) == 0

    def test_shuffle_queue(self, mock_player):
        tracks = [create_mock_track(f"Track {i}") for i in range(10)]
        mock_player.queue.put(tracks)

        count = QueueService.shuffle_queue(mock_player)
        assert count == 10
        assert len(mock_player.queue) == 10

    def test_shuffle_insufficient_tracks(self, mock_player):
        # Empty queue
        with pytest.raises(InputValidationError, match="At least 2 tracks are required"):
            QueueService.shuffle_queue(mock_player)

        # 1 track
        mock_player.queue.put(create_mock_track("Solo Track"))
        with pytest.raises(InputValidationError, match="At least 2 tracks are required"):
            QueueService.shuffle_queue(mock_player)

    def test_calculate_remaining_duration(self, mock_player):
        # Current track: 200,000ms total, at position 50,000ms -> 150,000ms remaining
        current = create_mock_track("Playing", length_ms=200000)
        mock_player.current = current
        mock_player.position = 50000

        # Queue has two tracks: 100,000ms and 60,000ms
        q1 = create_mock_track("Next 1", length_ms=100000)
        q2 = create_mock_track("Next 2", length_ms=60000)
        mock_player.queue.put([q1, q2])

        total = QueueService.calculate_remaining_duration(mock_player)
        assert total == 150000 + 100000 + 60000

    def test_get_queue_slice_pagination(self, mock_player):
        tracks = [create_mock_track(f"Track {i}") for i in range(25)]
        mock_player.queue.put(tracks)

        # Page 1 (10 per page) -> tracks 0..9
        p1_tracks, cur_p, total_p = QueueService.get_queue_slice(mock_player, page=1, per_page=10)
        assert len(p1_tracks) == 10
        assert p1_tracks[0] == tracks[0]
        assert cur_p == 1
        assert total_p == 3

        # Page 3 -> tracks 20..24
        p3_tracks, cur_p, total_p = QueueService.get_queue_slice(mock_player, page=3, per_page=10)
        assert len(p3_tracks) == 5
        assert p3_tracks[0] == tracks[20]
        assert cur_p == 3

        # Out of bounds clamps to max page
        p_clamped, cur_p, _ = QueueService.get_queue_slice(mock_player, page=99, per_page=10)
        assert cur_p == 3
        assert len(p_clamped) == 5


class TestFormatters:
    """Test suite for duration formatting and progress bar rendering."""

    def test_format_duration(self):
        assert format_duration(0) == "00:00"
        assert format_duration(65000) == "01:05"
        assert format_duration(3665000) == "01:01:05"

    def test_render_progress_bar_standard(self):
        # 50% through track
        bar = render_progress_bar(current_ms=100000, total_ms=200000, bar_length=10)
        assert "🔘" in bar
        assert "01:40" in bar
        assert "03:20" in bar

    def test_render_progress_bar_live_stream(self):
        bar = render_progress_bar(current_ms=0, total_ms=0)
        assert "LIVE" in bar

"""VOIDKAGE MUSIC - Queue Management Service.

Provides thread/async-safe queue operations, loop transitions, track removal,
shuffling, and pagination helpers over Wavelink's Queue.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional, Tuple

import wavelink

from utils.validators import InputValidationError, validate_position

if TYPE_CHECKING:
    from wavelink import Playable, Player


class LoopMode(enum.Enum):
    """Supported playback repetition modes."""

    OFF = "off"
    TRACK = "track"
    QUEUE = "queue"


class QueueService:
    """Encapsulates queue mutations and querying for VOIDKAGE music players."""

    @staticmethod
    def set_loop_mode(player: Player, mode: str | LoopMode) -> Tuple[wavelink.QueueMode, str]:
        """Configure the player's loop repetition mode.

        Args:
            player: The active Wavelink player.
            mode: Desired mode ('off', 'track', 'queue', or LoopMode enum).

        Returns:
            Tuple of (wavelink.QueueMode, user-friendly description string).

        Raises:
            InputValidationError: If the requested mode is unsupported.
        """
        if isinstance(mode, LoopMode):
            mode_str = mode.value
        else:
            mode_str = str(mode).lower().strip()

        if mode_str in ("off", "none", "disable"):
            player.queue.mode = wavelink.QueueMode.normal
            return wavelink.QueueMode.normal, "Looping disabled (Playback will proceed normally)."

        elif mode_str in ("track", "song", "single"):
            player.queue.mode = wavelink.QueueMode.loop
            return wavelink.QueueMode.loop, "Current track loop enabled (Track will repeat until skipped)."

        elif mode_str in ("queue", "all"):
            player.queue.mode = wavelink.QueueMode.loop_all
            return wavelink.QueueMode.loop_all, "Queue loop enabled (Upcoming tracks will loop continuously)."

        else:
            raise InputValidationError(
                f"Unknown loop mode: '{mode}'. Supported modes are: `off`, `track`, or `queue`."
            )

    @staticmethod
    def remove_at(player: Player, position: int) -> Playable:
        """Remove a track from the queue by its 1-based index position.

        Args:
            player: The active Wavelink player.
            position: 1-based index provided by the user.

        Returns:
            The removed Playable track.

        Raises:
            InputValidationError: If position is invalid or queue is empty.
        """
        queue_len = len(player.queue)
        zero_idx = validate_position(position, queue_len)

        # Retrieve the track before deletion
        track = list(player.queue)[zero_idx]
        player.queue.delete(zero_idx)
        return track

    @staticmethod
    def clear_queue(player: Player) -> int:
        """Clear all upcoming tracks from the queue without interrupting current playback.

        Args:
            player: The active Wavelink player.

        Returns:
            The number of tracks removed.
        """
        count = len(player.queue)
        player.queue.clear()
        return count

    @staticmethod
    def shuffle_queue(player: Player) -> int:
        """Randomize the order of upcoming tracks in the queue.

        Args:
            player: The active Wavelink player.

        Returns:
            The number of tracks shuffled.

        Raises:
            InputValidationError: If fewer than 2 tracks exist in queue.
        """
        count = len(player.queue)
        if count < 2:
            raise InputValidationError("At least 2 tracks are required in the queue to shuffle.")

        player.queue.shuffle()
        return count

    @staticmethod
    def calculate_remaining_duration(player: Player) -> int:
        """Calculate total remaining duration of active playback and upcoming queue in ms."""
        total_ms = sum(t.length for t in player.queue if not t.is_stream)
        if player.current and not player.current.is_stream:
            current_rem = max(0, player.current.length - (player.position or 0))
            total_ms += current_rem
        return total_ms

    @staticmethod
    def get_queue_slice(
        player: Player, page: int = 1, per_page: int = 10
    ) -> Tuple[List[Playable], int, int]:
        """Retrieve a paginated slice of upcoming tracks.

        Returns:
            Tuple of (tracks_on_page, current_page, total_pages).
        """
        total_tracks = len(player.queue)
        total_pages = max((total_tracks + per_page - 1) // per_page, 1)
        clamped_page = max(min(page, total_pages), 1)

        start = (clamped_page - 1) * per_page
        end = min(start + per_page, total_tracks)

        tracks = list(player.queue)[start:end]
        return tracks, clamped_page, total_pages

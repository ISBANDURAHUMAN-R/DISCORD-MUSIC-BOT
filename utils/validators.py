"""Void Vibe — Validation Utilities.

Validates voice channel states, permissions, inputs (volume, queue positions),
and moderation privileges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import discord

if TYPE_CHECKING:
    import wavelink


class VoiceValidationError(Exception):
    """Raised when voice channel conditions or permissions fail."""

    def __init__(self, message: str, ephemeral: bool = True):
        super().__init__(message)
        self.message = message
        self.ephemeral = ephemeral


class InputValidationError(Exception):
    """Raised when user-supplied command arguments fail validation."""

    def __init__(self, message: str, ephemeral: bool = True):
        super().__init__(message)
        self.message = message
        self.ephemeral = ephemeral


def validate_volume(volume: int) -> int:
    """Validate that volume is an integer between 0 and 100.

    Raises:
        InputValidationError: If out of range.
    """
    if not isinstance(volume, int):
        try:
            volume = int(volume)
        except (ValueError, TypeError):
            raise InputValidationError("Volume must be a valid whole number between 0 and 100.")

    if not 0 <= volume <= 100:
        raise InputValidationError(f"Volume must be between 0% and 100%. Received: {volume}%.")

    return volume


def validate_position(position: int, max_length: int) -> int:
    """Validate 1-based queue index against the current queue length.

    Returns:
        0-based index if valid.

    Raises:
        InputValidationError: If the position is out of bounds or queue is empty.
    """
    if max_length == 0:
        raise InputValidationError("The queue is currently empty. There are no tracks to remove.")

    if not 1 <= position <= max_length:
        raise InputValidationError(
            f"Invalid queue position: {position}. Please choose a position between 1 and {max_length}."
        )

    return position - 1


def is_privileged_or_dj(interaction: discord.Interaction) -> bool:
    """Check if the interacting member has elevated music controls.

    Permitted if:
    - Member has Administrator or Manage Channels permission.
    - Member has a role named 'DJ' (case-insensitive).
    - Member is the guild owner.
    """
    if not isinstance(interaction.user, discord.Member):
        return False

    member: discord.Member = interaction.user

    # Guild owner or admin
    if member.id == interaction.guild.owner_id:
        return True

    permissions = member.guild_permissions
    if permissions.administrator or permissions.manage_channels or permissions.manage_guild:
        return True

    # DJ role check
    has_dj_role = any(role.name.lower() == "dj" for role in member.roles)
    return has_dj_role


def ensure_voice_channel(
    interaction: discord.Interaction,
    require_same_channel: bool = True,
) -> discord.VoiceChannel | discord.StageChannel:
    """Validate that the user is in an accessible voice channel and handles bot channel state.

    Args:
        interaction: The command interaction.
        require_same_channel: If True and the bot is already connected to voice,
                              the user must be in the same channel as the bot.

    Returns:
        The target voice/stage channel.

    Raises:
        VoiceValidationError: If any condition fails.
    """
    if not interaction.guild:
        raise VoiceValidationError("Music commands can only be used inside a Discord server.")

    if not isinstance(interaction.user, discord.Member):
        raise VoiceValidationError("Unable to identify server member.")

    member: discord.Member = interaction.user
    if not member.voice or not member.voice.channel:
        raise VoiceValidationError(
            "You must join a voice channel first before using music commands."
        )

    user_channel = member.voice.channel
    bot_member = interaction.guild.me

    # Check bot permissions in target channel
    bot_perms = user_channel.permissions_for(bot_member)
    if not bot_perms.view_channel:
        raise VoiceValidationError(f"I do not have permission to view {user_channel.mention}.")
    if not bot_perms.connect:
        raise VoiceValidationError(f"I do not have permission to connect to {user_channel.mention}.")
    if not bot_perms.speak:
        raise VoiceValidationError(f"I do not have permission to speak in {user_channel.mention}.")

    # Check if bot is already connected to voice in this guild
    bot_voice = interaction.guild.voice_client
    if bot_voice and bot_voice.channel:
        if require_same_channel and bot_voice.channel.id != user_channel.id:
            # Check if user has moderator override
            if not is_privileged_or_dj(interaction):
                raise VoiceValidationError(
                    f"I am already playing in {bot_voice.channel.mention}. "
                    "You must be in the same voice channel to control playback."
                )

    return user_channel


def ensure_player_active(player: Optional[wavelink.Player]) -> wavelink.Player:
    """Ensure that the Wavelink player exists and is connected."""
    if not player or not player.connected:
        raise VoiceValidationError("There is no active music player connected in this server.")
    return player


def ensure_player_playing(player: Optional[wavelink.Player]) -> wavelink.Player:
    """Ensure that the player is active and currently playing a track."""
    player = ensure_player_active(player)
    if not player.current:
        raise VoiceValidationError("Nothing is currently playing.")
    return player

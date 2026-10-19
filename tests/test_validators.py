"""Unit tests for Void Vibe validators."""


from unittest.mock import MagicMock
import discord
import pytest

from utils.validators import (
    InputValidationError,
    VoiceValidationError,
    ensure_player_active,
    ensure_player_playing,
    ensure_voice_channel,
    is_privileged_or_dj,
    validate_position,
    validate_volume,
)


class TestValidators:
    """Test suite for volume, queue index, voice state, and permission validation."""

    def test_validate_volume_valid_ranges(self):
        assert validate_volume(0) == 0
        assert validate_volume(50) == 50
        assert validate_volume(100) == 100
        assert validate_volume("75") == 75

    def test_validate_volume_out_of_bounds(self):
        with pytest.raises(InputValidationError, match="between 0% and 100%"):
            validate_volume(-1)

        with pytest.raises(InputValidationError, match="between 0% and 100%"):
            validate_volume(101)

    def test_validate_volume_invalid_types(self):
        with pytest.raises(InputValidationError, match="valid whole number"):
            validate_volume("invalid_number")

    def test_validate_position_valid(self):
        # 1-based index 1 in queue of 5 -> 0-based index 0
        assert validate_position(1, 5) == 0
        # 1-based index 5 in queue of 5 -> 0-based index 4
        assert validate_position(5, 5) == 4
        # 1-based index 3 in queue of 5 -> 0-based index 2
        assert validate_position(3, 5) == 2

    def test_validate_position_empty_queue(self):
        with pytest.raises(InputValidationError, match="queue is currently empty"):
            validate_position(1, 0)

    def test_validate_position_out_of_bounds(self):
        with pytest.raises(InputValidationError, match="Invalid queue position"):
            validate_position(0, 5)

        with pytest.raises(InputValidationError, match="Invalid queue position"):
            validate_position(6, 5)

    def test_is_privileged_or_dj_owner(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.owner_id = 12345
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        assert is_privileged_or_dj(interaction) is True

    def test_is_privileged_or_dj_admin(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.owner_id = 99999
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.user.guild_permissions = MagicMock(spec=discord.Permissions)
        interaction.user.guild_permissions.administrator = True
        interaction.user.guild_permissions.manage_channels = False
        interaction.user.guild_permissions.manage_guild = False
        assert is_privileged_or_dj(interaction) is True

    def test_is_privileged_or_dj_role(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.owner_id = 99999
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.user.guild_permissions = MagicMock(spec=discord.Permissions)
        interaction.user.guild_permissions.administrator = False
        interaction.user.guild_permissions.manage_channels = False
        interaction.user.guild_permissions.manage_guild = False

        dj_role = MagicMock(spec=discord.Role)
        dj_role.name = "DJ"
        interaction.user.roles = [dj_role]

        assert is_privileged_or_dj(interaction) is True

    def test_is_privileged_or_dj_regular_member(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.owner_id = 99999
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.user.guild_permissions = MagicMock(spec=discord.Permissions)
        interaction.user.guild_permissions.administrator = False
        interaction.user.guild_permissions.manage_channels = False
        interaction.user.guild_permissions.manage_guild = False

        regular_role = MagicMock(spec=discord.Role)
        regular_role.name = "Member"
        interaction.user.roles = [regular_role]

        assert is_privileged_or_dj(interaction) is False

    def test_ensure_player_active_success(self):
        player = MagicMock()
        player.connected = True
        assert ensure_player_active(player) == player

    def test_ensure_player_active_failure(self):
        with pytest.raises(VoiceValidationError, match="no active music player"):
            ensure_player_active(None)

        disconnected_player = MagicMock()
        disconnected_player.connected = False
        with pytest.raises(VoiceValidationError, match="no active music player"):
            ensure_player_active(disconnected_player)

    def test_ensure_player_playing_failure(self):
        player = MagicMock()
        player.connected = True
        player.current = None
        with pytest.raises(VoiceValidationError, match="Nothing is currently playing"):
            ensure_player_playing(player)

    def test_ensure_voice_channel_not_in_voice(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.voice = None
        with pytest.raises(VoiceValidationError, match="join a voice channel first"):
            ensure_voice_channel(interaction)

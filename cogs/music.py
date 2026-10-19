"""VOIDKAGE MUSIC - Core Slash Commands and Audio Lifecycle Cog.

Implements all music commands (/play, /pause, /resume, /skip, /stop, /queue,
/nowplaying, /volume, /clear, /remove, /shuffle, /loop, /join, /leave)
and handles Lavalink node and playback lifecycle events.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
import wavelink

from cogs.player_controls import VoidkageControlView
from services.music_service import (
    MusicService,
    MusicServiceError,
    NoTracksFoundError,
    SourceUnavailableError,
)
from services.queue_service import QueueService
from utils.embeds import (
    error_embed,
    format_duration,
    info_embed,
    now_playing_embed,
    playlist_queued_embed,
    queue_embed,
    success_embed,
    track_queued_embed,
    warning_embed,
)
from utils.validators import (
    InputValidationError,
    VoiceValidationError,
    ensure_player_active,
    ensure_player_playing,
    ensure_voice_channel,
    is_privileged_or_dj,
    validate_volume,
)

if TYPE_CHECKING:
    from bot import VoidkageBot

logger = logging.getLogger("voidkage.music_cog")


class MusicCog(commands.Cog, name="Music"):
    """Core music playback and queue management commands."""

    def __init__(self, bot: VoidkageBot) -> None:
        self.bot = bot

    # ==========================================================================
    # WAVELINK EVENT LISTENERS
    # ==========================================================================

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        """Fired when a Lavalink node successfully establishes a websocket connection."""
        node = payload.node
        logger.info(
            "Lavalink Node '%s' is READY. Resumed: %s | Session: %s",
            node.identifier,
            payload.resumed,
            payload.session_id,
        )

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Fired when a track begins playing on any player."""
        player = payload.player
        track = payload.track
        if not player or not player.guild:
            return

        logger.info(
            "[Guild %s] Track Started: '%s' by '%s'",
            player.guild.id,
            track.title,
            track.author,
        )

        # Notify home channel if configured and track was auto-advanced from queue
        home_channel: Optional[discord.TextChannel] = getattr(player, "home_channel", None)
        if home_channel and getattr(player, "_auto_advanced", False):
            player._auto_advanced = False  # Reset flag
            try:
                view = VoidkageControlView(player, self.bot)
                embed = now_playing_embed(player, track)
                view.message = await home_channel.send(embed=embed, view=view)
            except (discord.HTTPException, discord.Forbidden):
                logger.warning("Failed to dispatch auto-advance embed to home channel.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """Fired when a track finishes, stops, or gets replaced."""
        player = payload.player
        if not player or not player.guild:
            return

        logger.debug(
            "[Guild %s] Track Ended: '%s' (Reason: %s)",
            player.guild.id,
            payload.track.title,
            payload.reason,
        )

        # Mark that the next track starting will be an auto-advance from the queue
        if payload.reason in ("finished", "loadFailed"):
            setattr(player, "_auto_advanced", True)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(
        self, payload: wavelink.TrackExceptionEventPayload
    ) -> None:
        """Fired when Lavalink encounters an exception streaming a track."""
        player = payload.player
        track = payload.track
        exc = payload.exception
        logger.error(
            "[Guild %s] Track Exception on '%s': %s",
            player.guild.id if player and player.guild else "Unknown",
            track.title,
            exc,
        )

        home_channel: Optional[discord.TextChannel] = getattr(player, "home_channel", None)
        if home_channel:
            try:
                msg = f"Playback failed for **{track.title}**. Attempting next track..."
                await home_channel.send(embed=warning_embed("Track Playback Error", msg))
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        """Fired when a player has been idle with an empty queue for the inactivity timeout."""
        if not player or not player.guild:
            return

        logger.info("[Guild %s] Inactivity timeout expired. Disconnecting player.", player.guild.id)
        home_channel: Optional[discord.TextChannel] = getattr(player, "home_channel", None)
        if home_channel:
            try:
                embed = info_embed(
                    "Disconnected Due to Inactivity",
                    "Playback finished and the queue remained empty. "
                    "Disconnected to conserve bandwidth.",
                )
                await home_channel.send(embed=embed)
            except discord.HTTPException:
                pass

        try:
            await player.disconnect()
        except Exception as exc:
            logger.warning("Error disconnecting inactive player: %s", exc)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Auto-disconnect if all human listeners leave the voice channel."""
        # Only inspect voice channel leaves
        if not before.channel or before.channel == after.channel:
            return

        guild = member.guild
        bot_voice: Optional[wavelink.Player] = guild.voice_client  # type: ignore

        if not bot_voice or not bot_voice.channel:
            return

        # Check if the channel that lost a member is the bot's channel
        if before.channel.id == bot_voice.channel.id:
            human_members = [m for m in bot_voice.channel.members if not m.bot]
            if len(human_members) == 0:
                logger.info(
                    "[Guild %s] Channel is now empty of human listeners. Cleaning up player.",
                    guild.id,
                )
                home_channel: Optional[discord.TextChannel] = getattr(bot_voice, "home_channel", None)
                if home_channel:
                    try:
                        await home_channel.send(
                            embed=info_embed(
                                "Voice Channel Abandoned",
                                "All listeners have left the voice channel. "
                                "Playback stopped and player disconnected.",
                            )
                        )
                    except discord.HTTPException:
                        pass
                bot_voice.queue.clear()
                await bot_voice.disconnect()

    # ==========================================================================
    # CORE SLASH COMMANDS
    # ==========================================================================

    @app_commands.command(name="play", description="Search and play a song, playlist, or stream URL.")
    @app_commands.describe(query="The song title, artist, or URL to play")
    async def play_command(self, interaction: discord.Interaction, query: str) -> None:
        """Search music providers or resolve URLs and play immediately or enqueue."""
        await interaction.response.defer()

        # Voice validation: user must be in a voice channel
        voice_channel = ensure_voice_channel(interaction, require_same_channel=False)

        player: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        # Connect or move to channel if needed
        if not player or not player.connected:
            player = await voice_channel.connect(cls=wavelink.Player)
            player.autoplay = wavelink.AutoPlayMode.partial
            setattr(player, "home_channel", interaction.channel)
        elif player.channel.id != voice_channel.id:
            if not is_privileged_or_dj(interaction):
                raise VoiceValidationError(
                    f"I am already playing in {player.channel.mention}. "
                    "You must be in the same voice channel to request songs."
                )
            await player.move_to(voice_channel)

        setattr(player, "home_channel", interaction.channel)

        # Search for tracks using music service
        member: discord.Member = interaction.user  # type: ignore
        search_result = await MusicService.search(query, requester=member)

        # Case 1: Playlist
        if search_result.is_playlist and search_result.playlist:
            playlist = search_result.playlist
            tracks = search_result.tracks
            total_duration_ms = sum(t.length for t in tracks if not t.is_stream)

            if not player.playing and not player.paused:
                # Play first track immediately
                first_track = tracks[0]
                await player.play(first_track)

                # Enqueue the remaining tracks
                for track in tracks[1:]:
                    await player.queue.put_wait(track)
            else:
                for track in tracks:
                    await player.queue.put_wait(track)

            embed = playlist_queued_embed(
                name=playlist.name or query,
                count=len(tracks),
                total_ms=total_duration_ms,
                requester_mention=member.mention,
                artwork=getattr(playlist, "artwork", None) or getattr(tracks[0], "artwork", None),
            )
            await interaction.followup.send(embed=embed)
            return

        # Case 2: Single Track
        track = search_result.tracks[0]

        if not player.playing and not player.paused:
            await player.play(track)
            view = VoidkageControlView(player, self.bot)
            embed = now_playing_embed(player, track)
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message = msg
        else:
            await player.queue.put_wait(track)
            queue_pos = len(player.queue)
            est_wait_ms = QueueService.calculate_remaining_duration(player) - track.length
            embed = track_queued_embed(track, queue_pos, max(est_wait_ms, 0))
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="pause", description="Pause the currently playing track.")
    async def pause_command(self, interaction: discord.Interaction) -> None:
        """Pause playback."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_playing(interaction.guild.voice_client)  # type: ignore

        if player.paused:
            await interaction.response.send_message(
                embed=warning_embed("Already Paused", "Playback is already paused. Use `/resume` to continue."),
                ephemeral=True,
            )
            return

        await player.pause(True)
        await interaction.response.send_message(
            embed=success_embed("Playback Paused", f"Paused: **{player.current.title}**")
        )

    @app_commands.command(name="resume", description="Resume currently paused playback.")
    async def resume_command(self, interaction: discord.Interaction) -> None:
        """Resume paused playback."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        if not player.paused:
            await interaction.response.send_message(
                embed=warning_embed("Not Paused", "Playback is already running."), ephemeral=True
            )
            return

        await player.pause(False)
        track_name = player.current.title if player.current else "Track"
        await interaction.response.send_message(
            embed=success_embed("Playback Resumed", f"Resumed: **{track_name}**")
        )

    @app_commands.command(name="skip", description="Skip the current track and advance the queue.")
    async def skip_command(self, interaction: discord.Interaction) -> None:
        """Skip the active track."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_playing(interaction.guild.voice_client)  # type: ignore

        skipped_track = player.current
        await player.skip(force=True)

        await interaction.response.send_message(
            embed=success_embed(
                "Track Skipped",
                f"Skipped: **[{skipped_track.title}]({skipped_track.uri or 'https://discord.com'})**",
            )
        )

    @app_commands.command(name="stop", description="Stop playback, clear the queue, and disconnect.")
    async def stop_command(self, interaction: discord.Interaction) -> None:
        """Halt playback and disconnect bot."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        player.queue.clear()
        await player.disconnect()

        await interaction.response.send_message(
            embed=success_embed(
                "Playback Stopped",
                "Cleared the upcoming queue and disconnected from the voice channel.",
            )
        )

    @app_commands.command(name="queue", description="Display the current track and upcoming queue.")
    @app_commands.describe(page="Page number of the queue to view (Default: 1)")
    async def queue_command(self, interaction: discord.Interaction, page: int = 1) -> None:
        """Display server queue with pagination."""
        player: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore
        if not player or not player.connected:
            await interaction.response.send_message(
                embed=info_embed("Queue Empty", "There is no active music player in this server."),
                ephemeral=True,
            )
            return

        embed = queue_embed(player, page=page, per_page=10)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="nowplaying",
        description="Display details, progress, and interactive controls for the current track.",
    )
    async def nowplaying_command(self, interaction: discord.Interaction) -> None:
        """Display real-time now playing embed with interactive buttons."""
        player: wavelink.Player = ensure_player_playing(interaction.guild.voice_client)  # type: ignore

        view = VoidkageControlView(player, self.bot)
        embed = now_playing_embed(player, player.current)
        msg = await interaction.response.send_message(embed=embed, view=view)
        # Note: on slash command send_message, fetch message if view needs reference
        try:
            view.message = await interaction.original_response()
        except discord.HTTPException:
            pass

    @app_commands.command(name="volume", description="Adjust the playback volume (0 - 100%).")
    @app_commands.describe(value="Volume percentage between 0 and 100")
    async def volume_command(self, interaction: discord.Interaction, value: int) -> None:
        """Change playback volume."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        valid_vol = validate_volume(value)
        await player.set_volume(valid_vol)

        await interaction.response.send_message(
            embed=success_embed("Volume Adjusted", f"Volume set to **{valid_vol}%** 🔊")
        )

    @app_commands.command(name="clear", description="Clear upcoming tracks from the queue.")
    async def clear_command(self, interaction: discord.Interaction) -> None:
        """Clear the queue without interrupting current song."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        count = QueueService.clear_queue(player)
        await interaction.response.send_message(
            embed=success_embed("Queue Cleared", f"Removed **{count}** upcoming tracks from the queue.")
        )

    @app_commands.command(
        name="remove", description="Remove a specific track from the queue by its position."
    )
    @app_commands.describe(position="The 1-based position number of the song in /queue")
    async def remove_command(self, interaction: discord.Interaction, position: int) -> None:
        """Remove a track by 1-based position."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        removed_track = QueueService.remove_at(player, position)
        await interaction.response.send_message(
            embed=success_embed(
                "Track Removed",
                f"Removed **#{position}**: [{removed_track.title}]({removed_track.uri or 'https://discord.com'})",
            )
        )

    @app_commands.command(name="shuffle", description="Shuffle upcoming tracks in the queue.")
    async def shuffle_command(self, interaction: discord.Interaction) -> None:
        """Shuffle queue."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        count = QueueService.shuffle_queue(player)
        await interaction.response.send_message(
            embed=success_embed("Queue Shuffled", f"Successfully shuffled **{count}** tracks in the queue. 🔀")
        )

    @app_commands.command(name="loop", description="Configure loop mode: off, track, or queue.")
    @app_commands.describe(mode="Choose repetition mode")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Off — Normal sequential playback", value="off"),
            app_commands.Choice(name="Track — Loop current song repeatedly", value="track"),
            app_commands.Choice(name="Queue — Loop entire server queue", value="queue"),
        ]
    )
    async def loop_command(
        self, interaction: discord.Interaction, mode: app_commands.Choice[str]
    ) -> None:
        """Set loop mode."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        _, desc = QueueService.set_loop_mode(player, mode.value)
        await interaction.response.send_message(
            embed=success_embed(f"Loop Mode: {mode.name.split(' ')[0]}", desc)
        )

    @app_commands.command(name="join", description="Connect to your current voice channel.")
    async def join_command(self, interaction: discord.Interaction) -> None:
        """Connect to voice channel."""
        voice_channel = ensure_voice_channel(interaction, require_same_channel=False)
        player: Optional[wavelink.Player] = interaction.guild.voice_client  # type: ignore

        if player and player.connected:
            if player.channel.id == voice_channel.id:
                await interaction.response.send_message(
                    embed=info_embed("Already Connected", f"I am already in {voice_channel.mention}."),
                    ephemeral=True,
                )
                return
            if not is_privileged_or_dj(interaction):
                raise VoiceValidationError(
                    f"I am active in {player.channel.mention}. "
                    "Only DJs or Administrators can move the bot to another channel."
                )
            await player.move_to(voice_channel)
            await interaction.response.send_message(
                embed=success_embed("Moved Channel", f"Moved to {voice_channel.mention}.")
            )
            return

        player = await voice_channel.connect(cls=wavelink.Player)
        player.autoplay = wavelink.AutoPlayMode.partial
        setattr(player, "home_channel", interaction.channel)

        await interaction.response.send_message(
            embed=success_embed("Connected", f"Joined {voice_channel.mention} and ready for music! 🌌")
        )

    @app_commands.command(name="leave", description="Disconnect from the voice channel and clean up.")
    async def leave_command(self, interaction: discord.Interaction) -> None:
        """Disconnect bot from voice."""
        ensure_voice_channel(interaction, require_same_channel=True)
        player: wavelink.Player = ensure_player_active(interaction.guild.voice_client)  # type: ignore

        player.queue.clear()
        await player.disconnect()

        await interaction.response.send_message(
            embed=success_embed("Disconnected", "Left the voice channel and cleaned up the player.")
        )

    # ==========================================================================
    # ERROR HANDLER FOR SLASH COMMANDS
    # ==========================================================================

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Centralized error handling for all slash commands in this cog."""
        # Unwrap CommandInvokeError
        original = getattr(error, "original", error)

        if isinstance(original, VoiceValidationError):
            embed = error_embed("Voice Channel Error", original.message)
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=original.ephemeral)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=original.ephemeral)
            return

        if isinstance(original, InputValidationError):
            embed = error_embed("Input Validation Error", original.message)
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=original.ephemeral)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=original.ephemeral)
            return

        if isinstance(original, NoTracksFoundError):
            embed = error_embed("No Tracks Found", str(original))
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(original, SourceUnavailableError):
            embed = error_embed("Source Unavailable", str(original))
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(original, app_commands.BotMissingPermissions):
            missing_perms = ", ".join(original.missing_permissions)
            embed = error_embed(
                "Bot Missing Permissions",
                f"The bot is missing required Discord permissions: `{missing_perms}`",
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Unexpected internal errors - log full trace but do not leak secrets to users
        logger.error("Unhandled error in slash command '%s': %s", interaction.command.name if interaction.command else "unknown", original, exc_info=True)
        embed = error_embed(
            "Command Execution Error",
            "An unexpected error occurred while executing this command. "
            "The issue has been logged for review.",
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: VoidkageBot) -> None:
    """Extension entry point for loading the Music cog."""
    await bot.add_cog(MusicCog(bot))

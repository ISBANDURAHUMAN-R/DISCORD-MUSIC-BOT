"""VOIDKAGE MUSIC - Interactive Discord UI Components.

Provides real-time interactive buttons for Discord players with voice validation,
moderator permission checks, and dynamic UI state synchronization.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import discord
from discord import ui
import wavelink

from services.queue_service import QueueService
from utils.embeds import (
    COLOR_VOIDKAGE_PRIMARY,
    error_embed,
    now_playing_embed,
    queue_embed,
    success_embed,
)
from utils.validators import is_privileged_or_dj

if TYPE_CHECKING:
    from discord.ext import commands

logger = logging.getLogger("voidkage.player_controls")


class VoidkageControlView(ui.View):
    """Interactive Discord buttons attached to VOIDKAGE /nowplaying and playback embeds."""

    def __init__(
        self,
        player: wavelink.Player,
        bot: commands.Bot,
        timeout: Optional[float] = 600.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.player = player
        self.bot = bot
        self.message: Optional[discord.Message] = None
        self._sync_button_states()

    def _sync_button_states(self) -> None:
        """Update button labels and colors based on player state."""
        # Pause / Resume button
        pause_btn: Optional[ui.Button] = discord.utils.get(self.children, custom_id="btn_pause_resume")
        if pause_btn:
            if self.player.paused:
                pause_btn.label = "Resume"
                pause_btn.emoji = "▶️"
                pause_btn.style = discord.ButtonStyle.success
            else:
                pause_btn.label = "Pause"
                pause_btn.emoji = "⏸️"
                pause_btn.style = discord.ButtonStyle.secondary

        # Loop button
        loop_btn: Optional[ui.Button] = discord.utils.get(self.children, custom_id="btn_loop")
        if loop_btn:
            mode = self.player.queue.mode
            if mode == wavelink.QueueMode.loop:
                loop_btn.label = "Loop: Track"
                loop_btn.style = discord.ButtonStyle.primary
            elif mode == wavelink.QueueMode.loop_all:
                loop_btn.label = "Loop: Queue"
                loop_btn.style = discord.ButtonStyle.primary
            else:
                loop_btn.label = "Loop: Off"
                loop_btn.style = discord.ButtonStyle.secondary

    async def _validate_interaction(self, interaction: discord.Interaction) -> bool:
        """Enforce strict voice channel and DJ/moderator checks on button clicks."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                embed=error_embed("Access Denied", "Buttons can only be used in servers."),
                ephemeral=True,
            )
            return False

        member: discord.Member = interaction.user

        # User voice check
        if not member.voice or not member.voice.channel:
            await interaction.response.send_message(
                embed=error_embed(
                    "Voice Channel Required",
                    "You must be in a voice channel to use music controls.",
                ),
                ephemeral=True,
            )
            return False

        # Same voice channel check
        bot_voice = interaction.guild.voice_client
        if not bot_voice or not bot_voice.channel:
            await interaction.response.send_message(
                embed=error_embed("Player Inactive", "The music player is no longer connected."),
                ephemeral=True,
            )
            return False

        if bot_voice.channel.id != member.voice.channel.id:
            if not is_privileged_or_dj(interaction):
                await interaction.response.send_message(
                    embed=error_embed(
                        "Wrong Voice Channel",
                        f"You must join {bot_voice.channel.mention} to control music playback.",
                    ),
                    ephemeral=True,
                )
                return False

        return True

    @ui.button(
        label="Pause",
        emoji="⏸️",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_pause_resume",
        row=0,
    )
    async def pause_resume_button(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        """Toggle playback between paused and playing."""
        if not await self._validate_interaction(interaction):
            return

        if not self.player.current:
            await interaction.response.send_message(
                embed=error_embed("No Track", "No track is currently playing."), ephemeral=True
            )
            return

        if self.player.paused:
            await self.player.pause(False)
            action_desc = "Resumed playback."
        else:
            await self.player.pause(True)
            action_desc = "Paused playback."

        self._sync_button_states()
        if self.player.current:
            embed = now_playing_embed(self.player, self.player.current)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @ui.button(
        label="Skip",
        emoji="⏭️",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_skip",
        row=0,
    )
    async def skip_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Skip the current track."""
        if not await self._validate_interaction(interaction):
            return

        if not self.player.current:
            await interaction.response.send_message(
                embed=error_embed("Cannot Skip", "Nothing is currently playing to skip."),
                ephemeral=True,
            )
            return

        skipped = self.player.current
        await self.player.skip(force=True)

        await interaction.response.send_message(
            embed=success_embed(
                "Track Skipped",
                f"Skipped: **[{skipped.title}]({skipped.uri or 'https://discord.com'})**",
            ),
            ephemeral=True,
        )

    @ui.button(
        label="Stop",
        emoji="⏹️",
        style=discord.ButtonStyle.danger,
        custom_id="btn_stop",
        row=0,
    )
    async def stop_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Stop playback, clear queue, and disconnect."""
        if not await self._validate_interaction(interaction):
            return

        self.player.queue.clear()
        await self.player.disconnect()

        # Disable all buttons
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True

        embed = success_embed(
            "Playback Stopped",
            "Playback has been stopped, queue cleared, and the bot disconnected.",
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @ui.button(
        label="Queue",
        emoji="📜",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_queue",
        row=0,
    )
    async def queue_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Display an ephemeral preview of the server queue."""
        if not await self._validate_interaction(interaction):
            return

        embed = queue_embed(self.player, page=1, per_page=10)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(
        label="Loop: Off",
        emoji="🔁",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_loop",
        row=0,
    )
    async def loop_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Cycle through loop modes: Normal -> Track Loop -> Queue Loop -> Normal."""
        if not await self._validate_interaction(interaction):
            return

        current_mode = self.player.queue.mode
        if current_mode == wavelink.QueueMode.normal:
            new_mode = "track"
        elif current_mode == wavelink.QueueMode.loop:
            new_mode = "queue"
        else:
            new_mode = "off"

        _, desc = QueueService.set_loop_mode(self.player, new_mode)
        self._sync_button_states()

        if self.player.current:
            embed = now_playing_embed(self.player, self.player.current)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                embed=success_embed("Loop Mode Changed", desc), ephemeral=True
            )

    async def on_timeout(self) -> None:
        """Disable buttons when the UI view times out to conserve resources."""
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

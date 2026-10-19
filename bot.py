"""VOIDKAGE MUSIC — High-Performance Discord Music Bot.

Built with Python 3.12+, discord.py 2.x, Wavelink 3.5, and Lavalink v4.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Optional

import discord
from discord.ext import commands
import wavelink

from config import Config, ConfigurationError


class VoidkageBot(commands.Bot):
    """Core Discord bot application for VOIDKAGE MUSIC."""

    def __init__(self, config: Config) -> None:
        self.config = config

        # Standard non-privileged Discord intents
        # Slash commands and voice state updates do not require Message Content intent.
        intents = discord.Intents.default()
        intents.voice_states = True

        super().__init__(
            command_prefix="!",  # Slash commands are primary; prefix exists for fallback
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        """Asynchronous setup hook executed before the bot logs into Discord."""
        # 1. Load extension cogs
        try:
            await self.load_extension("cogs.music")
            logging.info("Successfully loaded extension: cogs.music")
        except Exception as exc:
            logging.critical("Failed to load music cog: %s", exc, exc_info=True)
            raise exc

        # 2. Connect to Wavelink / Lavalink node pool
        logging.info("Connecting to Lavalink node at %s...", self.config.lavalink_uri)
        node = wavelink.Node(
            identifier="Voidkage-Node-1",
            uri=self.config.lavalink_uri,
            password=self.config.lavalink_password,
            inactive_player_timeout=self.config.inactivity_timeout,
        )

        try:
            await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)
            logging.info("Dispatched connection request to Lavalink pool.")
        except Exception as exc:
            logging.error(
                "Could not immediately connect to Lavalink at %s: %s. "
                "Wavelink will retry connection automatically in the background.",
                self.config.lavalink_uri,
                exc,
            )

        # 3. Synchronize Application Slash Commands
        if self.config.guild_id:
            guild_obj = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            logging.info(
                "Instantly synchronized %d slash commands to Dev Guild ID: %d",
                len(synced),
                self.config.guild_id,
            )
        else:
            synced = await self.tree.sync()
            logging.info("Synchronized %d global slash commands with Discord.", len(synced))

    async def on_ready(self) -> None:
        """Invoked when the bot has finished internal caching and is ready."""
        user_name = self.user.name if self.user else "VOIDKAGE"
        user_id = self.user.id if self.user else 0
        guild_count = len(self.guilds)

        logging.info("==============================================================")
        logging.info("🌌 %s is ONLINE and ready for commands! (ID: %s)", user_name, user_id)
        logging.info("Connected to %d Discord server(s).", guild_count)
        logging.info("==============================================================")

        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/play | VOIDKAGE",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def close(self) -> None:
        """Clean shutdown handler."""
        logging.info("Shutting down VOIDKAGE MUSIC bot. Cleaning up active players...")

        # Disconnect all active guild voice players
        for guild in self.guilds:
            voice_client: Optional[wavelink.Player] = guild.voice_client  # type: ignore
            if voice_client and voice_client.connected:
                try:
                    await voice_client.disconnect()
                except Exception:
                    pass

        # Close Wavelink Node Pool
        try:
            await wavelink.Pool.close()
        except Exception:
            pass

        await super().close()
        logging.info("VOIDKAGE MUSIC shutdown complete.")


def setup_logging(log_level: str) -> logging.Logger:
    """Configure structured console logging."""
    numeric_level = getattr(logging, log_level, logging.INFO)

    log_format = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    # Clear existing handlers to prevent duplicate lines
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress verbose discord gateway noise
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.INFO)

    return root_logger


def main() -> None:
    """Application main entry point."""
    try:
        config = Config.load()
    except ConfigurationError as exc:
        print(f"\n[FATAL CONFIGURATION ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)

    logger = setup_logging(config.log_level)
    config.print_diagnostics(logger)

    bot = VoidkageBot(config)

    try:
        bot.run(config.discord_token, log_handler=None)
    except discord.LoginFailure:
        logger.critical(
            "Discord rejected the provided DISCORD_TOKEN. "
            "Please check that your token in .env is valid and has not been reset."
        )
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Termination signal received. Exiting.")


if __name__ == "__main__":
    main()

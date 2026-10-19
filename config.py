"""VOIDKAGE MUSIC - Configuration Management Module.

Handles loading, validating, and sanitizing configuration variables
from the environment and .env file.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

# Pre-load environment variables from .env if present
load_dotenv()


class ConfigurationError(Exception):
    """Raised when one or more configuration values are invalid or missing."""


def _mask_secret(val: str, visible_chars: int = 4) -> str:
    """Mask a sensitive token or password, exposing only a short prefix and suffix."""
    if not val:
        return "<EMPTY>"
    if len(val) <= visible_chars * 2:
        return "*" * len(val)
    return f"{val[:visible_chars]}...{val[-visible_chars:]} (len: {len(val)})"


@dataclass(frozen=True)
class Config:
    """Immutable application configuration container."""

    discord_token: str
    lavalink_uri: str
    lavalink_password: str
    inactivity_timeout: int
    log_level: str
    default_volume: int
    guild_id: Optional[int]
    embed_color: int = 0x8B5CF6  # VOIDKAGE Neon Purple
    embed_color_error: int = 0xEF4444  # Crimson
    embed_color_success: int = 0x10B981  # Emerald
    embed_color_warning: int = 0xF59E0B  # Amber

    @classmethod
    def load(cls) -> Config:
        """Load and validate all configuration values from environment variables."""
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token or token == "your_discord_bot_token_here":
            raise ConfigurationError(
                "DISCORD_TOKEN is missing or set to the default placeholder in .env. "
                "Please configure a valid Discord Bot Token from the Developer Portal."
            )

        lavalink_uri = os.getenv("LAVALINK_URI", "http://127.0.0.1:2333").strip()
        parsed_uri = urlparse(lavalink_uri)
        if not parsed_uri.scheme or not parsed_uri.netloc:
            raise ConfigurationError(
                f"LAVALINK_URI '{lavalink_uri}' is invalid. "
                "It must include a scheme and host/port (e.g. 'http://127.0.0.1:2333')."
            )

        lavalink_password = os.getenv("LAVALINK_PASSWORD", "youshallnotpass").strip()
        if not lavalink_password:
            raise ConfigurationError("LAVALINK_PASSWORD cannot be empty.")

        inactivity_str = os.getenv("INACTIVITY_TIMEOUT", "300").strip()
        try:
            inactivity_timeout = int(inactivity_str)
            if inactivity_timeout < 0:
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                f"INACTIVITY_TIMEOUT must be a non-negative integer in seconds, got: '{inactivity_str}'."
            )

        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_log_levels:
            raise ConfigurationError(
                f"LOG_LEVEL must be one of {sorted(valid_log_levels)}, got: '{log_level}'."
            )

        volume_str = os.getenv("DEFAULT_VOLUME", "100").strip()
        try:
            default_volume = int(volume_str)
            if not 0 <= default_volume <= 100:
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                f"DEFAULT_VOLUME must be an integer between 0 and 100, got: '{volume_str}'."
            )

        guild_id_str = os.getenv("GUILD_ID", "").strip()
        guild_id: Optional[int] = None
        if guild_id_str:
            try:
                guild_id = int(guild_id_str)
            except ValueError:
                raise ConfigurationError(
                    f"GUILD_ID must be a numeric Discord snowflake ID, got: '{guild_id_str}'."
                )

        return cls(
            discord_token=token,
            lavalink_uri=lavalink_uri,
            lavalink_password=lavalink_password,
            inactivity_timeout=inactivity_timeout,
            log_level=log_level,
            default_volume=default_volume,
            guild_id=guild_id,
        )

    def print_diagnostics(self, logger: logging.Logger) -> None:
        """Print safe startup diagnostics without revealing secrets."""
        logger.info("================ VOIDKAGE MUSIC CONFIGURATION ================")
        logger.info("Discord Token:       %s", _mask_secret(self.discord_token))
        logger.info("Lavalink URI:        %s", self.lavalink_uri)
        logger.info("Lavalink Password:   %s", _mask_secret(self.lavalink_password))
        logger.info("Inactivity Timeout:  %ds", self.inactivity_timeout)
        logger.info("Log Level:           %s", self.log_level)
        logger.info("Default Volume:      %d%%", self.default_volume)
        logger.info("Dev Guild ID:        %s", self.guild_id or "Global Sync")
        logger.info("==============================================================")

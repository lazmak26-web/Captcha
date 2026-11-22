"""
Leakers$ CAPTCHA - Discord Bot Client
Subclasses commands.Bot with lifecycle hooks, persistent view binding, and cog loading.
"""

from __future__ import annotations

import logging
import discord
from discord.ext import commands

import config
from database import DatabaseManager
from captcha import CaptchaGenerator
from .session_manager import SessionManager
from .views.verify_button_view import VerifyButtonView

logger = logging.getLogger("leakers_captcha.client")


class LeakersCaptchaBot(commands.Bot):
    """Core Discord client with database integration and security managers."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True  # Required for role assignment and join detection
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.db = DatabaseManager(config.DATABASE_PATH)
        self.captcha_generator = CaptchaGenerator()
        self.session_manager = SessionManager()

        # Enforce channel restriction guard across all slash commands
        async def global_channel_guard(interaction: discord.Interaction) -> bool:
            if interaction.channel_id not in config.ALLOWED_CHANNEL_IDS:
                allowed_str = ", ".join(f"<#{cid}>" for cid in config.ALLOWED_CHANNEL_IDS)
                msg = f"❌ This bot can only be used in designated channels: {allowed_str}."
                if not interaction.response.is_done():
                    await interaction.response.send_message(msg, ephemeral=True)
                else:
                    await interaction.followup.send(msg, ephemeral=True)
                return False
            return True

        self.tree.interaction_check = global_channel_guard

    async def setup_hook(self) -> None:
        """Executed during bot startup before connecting to Discord gateway."""
        logger.info("Initializing database schema...")
        await self.db.initialize()

        logger.info("Registering persistent verification views...")
        self.add_view(VerifyButtonView(self))

        logger.info("Loading extension cogs...")
        cogs = [
            "bot.cogs.verification",
            "bot.cogs.admin",
            "bot.cogs.stats",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info("Loaded cog: %s", cog)
            except Exception as e:
                logger.exception("Failed to load cog %s: %s", cog, e)

        # Sync application slash commands with Discord
        try:
            logger.info("Syncing slash commands tree...")
            synced = await self.tree.sync()
            logger.info("Successfully synced %d global application command(s).", len(synced))
        except Exception as e:
            logger.warning("Could not sync command tree during setup: %s", e)

    async def on_ready(self) -> None:
        """Triggered once bot is connected and cache is primed."""
        if self.user:
            logger.info("Logged in as %s (ID: %s)", self.user.name, self.user.id)
            logger.info("Connected to %d guild(s).", len(self.guilds))

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Leakers$ Verification | /help",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)


"""
Leakers$ CAPTCHA - Statistics and Help Cog
Provides /stats and /help slash commands with visual analytics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

import config

if TYPE_CHECKING:
    from bot.client import LeakersCaptchaBot

logger = logging.getLogger("leakers_captcha.cogs.stats")


class StatsCog(commands.Cog, name="Analytics & Help"):
    """Statistical telemetry and guidance commands."""

    def __init__(self, bot: LeakersCaptchaBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="stats",
        description="Display verification analytics and pass/fail metrics for this server.",
    )
    async def stats(self, interaction: discord.Interaction) -> None:
        """Retrieves and calculates verification telemetry from SQLite."""
        if interaction.guild is None:
            await interaction.response.send_message("This command must be run inside a guild.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        data = await self.bot.db.get_guild_stats(interaction.guild.id)
        cfg = await self.bot.db.get_guild_config(interaction.guild.id)

        total = data["total"]
        passed = data["passed"]
        failed = data["failed"]
        expired = data["expired"]

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        embed = discord.Embed(
            title=f"📊 Verification Analytics: {interaction.guild.name}",
            description="Historical security verification metrics recorded for this server.",
            color=config.COLOR_PRIMARY,
        )

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        embed.add_field(name="Total Challenges", value=f"**{total:,}**", inline=True)
        embed.add_field(name="Passed Verifications", value=f"✅ **{passed:,}**", inline=True)
        embed.add_field(name="Failed / Timed Out", value=f"❌ **{failed + expired:,}**", inline=True)

        embed.add_field(name="Success Rate", value=f"📈 **{pass_rate:.1f}%**", inline=True)
        embed.add_field(name="Active Visual Style", value=f"`{cfg.captcha_style}`", inline=True)
        embed.add_field(name="Max Attempts Allowed", value=f"`{cfg.max_attempts}`", inline=True)

        embed.set_footer(text="Leakers$ Telemetry Engine")
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="help",
        description="Show setup instructions, security features, and list of supported styles.",
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Renders comprehensive documentation embed."""
        embed = discord.Embed(
            title="🛡️ Leakers$ CAPTCHA - Bot Documentation",
            description=(
                "**Leakers$ CAPTCHA** provides advanced visual verification inside Discord "
                "to safeguard your community against automated raids, bots, and spam."
            ),
            color=config.COLOR_PRIMARY,
        )

        embed.add_field(
            name="🚀 Quick Setup Guide",
            value=(
                "1. Run `/setup` specifying your target channel and verified role.\n"
                "2. Ensure the bot's role is placed **above** the verified role.\n"
                "3. Members click the persistent **Verify** button to receive their role."
            ),
            inline=False,
        )

        embed.add_field(
            name="📜 Slash Commands",
            value=(
                "• `/setup` - Configure verification channel, verified/unverified roles, and audit logs.\n"
                "• `/verify` - Start a verification challenge directly.\n"
                "• `/settings` - View or tweak visual styles, timeouts, attempts, and cooldowns.\n"
                "• `/stats` - View server verification analytics and success percentages.\n"
                "• `/help` - Display this interactive guide."
            ),
            inline=False,
        )

        styles_formatted = ", ".join(f"`{s}`" for s in config.SUPPORTED_STYLES)
        embed.add_field(
            name=f"🎨 13 Supported Visual Styles ({len(config.SUPPORTED_STYLES)})",
            value=f"{styles_formatted}\n*(Or set style to `Random` for dynamic rotation)*",
            inline=False,
        )

        embed.add_field(
            name="🔒 Security Architecture",
            value=(
                "• Cryptographically secure token generation (`secrets` module).\n"
                "• Single-use challenges with strict replay prevention.\n"
                "• Per-user session isolation & anti-spam rate limits.\n"
                "• Non-blocking asynchronous SQLite persistence (`aiosqlite`)."
            ),
            inline=False,
        )

        embed.set_footer(text="Leakers$ Security Systems | Discord.py 2.x")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: LeakersCaptchaBot) -> None:
    """Extension cog setup entry point."""
    await bot.add_cog(StatsCog(bot))


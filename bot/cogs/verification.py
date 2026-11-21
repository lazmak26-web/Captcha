"""
Leakers$ CAPTCHA - Verification Cog
Listens for member joins and provides the /verify slash command.
"""

from __future__ import annotations

import io
import logging
import discord
from discord import app_commands
from discord.ext import commands

import config
from bot.views.captcha_modal_view import CaptchaInteractionView, build_challenge_embed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.client import LeakersCaptchaBot

logger = logging.getLogger("leakers_captcha.cogs.verification")


class VerificationCog(commands.Cog, name="Verification"):
    """Core verification workflows, join role assignment, and direct /verify command."""

    def __init__(self, bot: LeakersCaptchaBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Automatically assigns unverified role to new members if configured."""
        if member.bot:
            return

        cfg = await self.bot.db.get_guild_config(member.guild.id)
        if cfg.unverified_role_id:
            role = member.guild.get_role(cfg.unverified_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Leakers$ CAPTCHA: Assign Unverified role on join")
                    logger.info("Assigned unverified role to %s in guild %s", member.id, member.guild.id)
                except discord.Forbidden:
                    logger.error("Lacking permissions to assign unverified role in %s", member.guild.id)

    @app_commands.command(
        name="verify",
        description="Initiate the CAPTCHA verification challenge to access this server.",
    )
    async def verify(self, interaction: discord.Interaction) -> None:
        """Slash command counterpart to the persistent verification button."""
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Anti-spam guard
        if self.bot.session_manager.is_rate_limited(guild_id, user_id, min_interval=1.5):
            await interaction.followup.send("Please slow down. Try again shortly.", ephemeral=True)
            return

        guild_cfg = await self.bot.db.get_guild_config(guild_id)
        if not guild_cfg.is_configured:
            await interaction.followup.send(
                "Verification is not yet configured for this server. Ask an admin to run `/setup`.",
                ephemeral=True,
            )
            return

        # Check if already verified
        if guild_cfg.verified_role_id:
            verified_role = interaction.guild.get_role(guild_cfg.verified_role_id)
            if verified_role and verified_role in interaction.user.roles:
                already_embed = discord.Embed(
                    title="Already Verified",
                    description="You are already verified in this server!",
                    color=config.COLOR_SUCCESS,
                )
                await interaction.followup.send(embed=already_embed, ephemeral=True)
                return

        # Check cooldown
        cooldown_left = self.bot.session_manager.get_cooldown_remaining(guild_id, user_id)
        if cooldown_left is not None:
            cooldown_embed = discord.Embed(
                title="Verification Cooldown",
                description=f"You must wait **{cooldown_left}s** before trying again.",
                color=config.COLOR_DANGER,
            )
            await interaction.followup.send(embed=cooldown_embed, ephemeral=True)
            return

        # Create or reuse session
        session = self.bot.session_manager.get_session(guild_id, user_id)
        if session is None or session.image_bytes is None:
            captcha_res = await self.bot.captcha_generator.create_captcha(style_name=guild_cfg.captcha_style)
            session = self.bot.session_manager.create_session(
                guild_id=guild_id,
                user_id=user_id,
                code=captcha_res.code,
                style_name=captcha_res.style_name,
                expiration_seconds=guild_cfg.expiration_seconds,
                max_attempts=guild_cfg.max_attempts,
                image_bytes=captcha_res.image_bytes,
            )
            raw_bytes = captcha_res.image_bytes
            style_name = captcha_res.style_name
        else:
            raw_bytes = session.image_bytes
            style_name = session.style_name

        file = discord.File(io.BytesIO(raw_bytes), filename="captcha.png")
        embed = build_challenge_embed(interaction.guild, style_name)

        interaction_view = CaptchaInteractionView(bot=self.bot, guild_config=guild_cfg)
        await interaction.followup.send(embed=embed, file=file, view=interaction_view, ephemeral=True)


async def setup(bot: LeakersCaptchaBot) -> None:
    """Extension cog setup entry point."""
    await bot.add_cog(VerificationCog(bot))


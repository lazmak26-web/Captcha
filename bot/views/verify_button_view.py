"""
Leakers$ CAPTCHA - Persistent Verification Button View
Listens indefinitely for member verification trigger button clicks.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING
import discord
from discord import ui

import config
from .captcha_modal_view import CaptchaInteractionView

if TYPE_CHECKING:
    from bot.client import LeakersCaptchaBot

logger = logging.getLogger("leakers_captcha.views.button")


class VerifyButtonView(ui.View):
    """
    Persistent button view displayed in the server's designated verification channel.
    Has timeout=None and an explicit custom_id to survive bot restarts.
    """

    def __init__(self, bot: LeakersCaptchaBot) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        website_emoji = discord.utils.get(bot.emojis, name="world_www") or discord.PartialEmoji(name="world_www", id=1573710974043684915)
        self.add_item(
            discord.ui.Button(
                label="Website",
                style=discord.ButtonStyle.link,
                url=config.WEBSITE_URL,
                emoji=website_emoji,
            )
        )

    @ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        emoji=discord.PartialEmoji(name="circle_check", id=1573712617585909791),
        custom_id="leakers_captcha:verify_btn",
    )
    async def verify_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Handles member interaction to start the CAPTCHA challenge."""
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Verification is only available within servers.", ephemeral=True)
            return

        if interaction.channel_id not in config.ALLOWED_CHANNEL_IDS:
            allowed_str = ", ".join(f"<#{cid}>" for cid in config.ALLOWED_CHANNEL_IDS)
            await interaction.response.send_message(
                f"❌ Verification is restricted to designated channels: {allowed_str}.",
                ephemeral=True,
            )
            return

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Anti-spam guard
        if self.bot.session_manager.is_rate_limited(guild_id, user_id, min_interval=1.5):
            await interaction.response.send_message("Please slow down. Try again in a couple of seconds.", ephemeral=True)
            return

        # Fetch guild configuration from SQLite
        guild_cfg = await self.bot.db.get_guild_config(guild_id)
        if not guild_cfg.is_configured:
            await interaction.response.send_message(
                "Verification is not fully configured for this server. Please ask an administrator to run `/setup`.",
                ephemeral=True,
            )
            return

        # Check if user already holds the verified role
        if guild_cfg.verified_role_id:
            verified_role = interaction.guild.get_role(guild_cfg.verified_role_id)
            if verified_role and verified_role in interaction.user.roles:
                already_embed = discord.Embed(
                    title="Already Verified",
                    description="You are already verified and have full access to the server!",
                    color=config.COLOR_SUCCESS,
                )
                await interaction.response.send_message(embed=already_embed, ephemeral=True)
                return

        # Check if user is in penalty cooldown
        cooldown_left = self.bot.session_manager.get_cooldown_remaining(guild_id, user_id)
        if cooldown_left is not None:
            cooldown_embed = discord.Embed(
                title="Verification Cooldown",
                description=(
                    f"You recently exceeded your maximum attempts.\n"
                    f"Please wait **{cooldown_left}s** before initiating a new verification challenge."
                ),
                color=config.COLOR_DANGER,
            )
            await interaction.response.send_message(embed=cooldown_embed, ephemeral=True)
            return

        # Check for existing valid session, or create a new one
        session = self.bot.session_manager.get_session(guild_id, user_id)
        if session is None or session.image_bytes is None:
            # Generate new challenge
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
        embed = discord.Embed(
            description=(
                "Follow the instruction printed inside the image, then enter the five "
                "requested digits in normal reading order (top left to right, then bottom left to right)."
            ),
            color=config.COLOR_PRIMARY,
        )
        if interaction.guild:
            embed.set_author(
                name=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
            )
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_image(url="attachment://captcha.png")

        interaction_view = CaptchaInteractionView(bot=self.bot, guild_config=guild_cfg)
        await interaction.response.send_message(embed=embed, file=file, view=interaction_view, ephemeral=True)


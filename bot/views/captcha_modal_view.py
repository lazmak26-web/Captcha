"""
Leakers$ CAPTCHA - Interactive Modal and Action Views
Handles user submission modals, code validation, and CAPTCHA re-generation.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Optional
import discord
from discord import ui

import config
from database import GuildConfig

if TYPE_CHECKING:
    from bot.client import LeakersCaptchaBot

logger = logging.getLogger("leakers_captcha.views.modal")


def build_challenge_embed(guild: Optional[discord.Guild], style_name: str) -> discord.Embed:
    """Builds the challenge embed with instructions matching the CAPTCHA style."""
    if style_name == "MarketShapes":
        description = (
            "Follow the instruction printed inside the image, then enter the five "
            "requested digits in normal reading order (top left to right, then bottom left to right)."
        )
    else:
        description = (
            "Enter the characters shown in the image, then click **Submit Code**. "
            "The code is not case-sensitive."
        )
    embed = discord.Embed(description=description, color=config.COLOR_PRIMARY)
    if guild:
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
    embed.set_image(url="attachment://captcha.png")
    return embed


class CaptchaCodeModal(ui.Modal, title="Leakers$ Security Verification"):
    """Modal prompt asking the user to submit the characters from the image."""

    captcha_input = ui.TextInput(
        label="Enter the code from the image",
        placeholder="e.g. 72946 or K7PX3M",
        min_length=2,
        max_length=12,
        required=True,
    )

    def __init__(self, bot: LeakersCaptchaBot, guild_config: GuildConfig) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_config = guild_config

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Processes submitted code against active user session."""
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Verification must occur inside a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        user_id = interaction.user.id
        submitted_code = self.captcha_input.value

        session = self.bot.session_manager.get_session(guild_id, user_id)
        if session is None:
            embed = discord.Embed(
                title="Session Expired",
                description="Your verification session has expired. Click **Verify** again to start over.",
                color=config.COLOR_DANGER,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        style_used = session.style_name
        attempts_used = (session.max_attempts - session.attempts_left) + 1

        is_correct, msg, attempts_left = self.bot.session_manager.evaluate_code(
            guild_id=guild_id,
            user_id=user_id,
            submission=submitted_code,
        )

        # Acknowledge within Discord's 3-second window before doing slow work
        await interaction.response.defer()

        if is_correct:
            # Grant verified role
            verified_role = interaction.guild.get_role(self.guild_config.verified_role_id or 0)
            unverified_role = interaction.guild.get_role(self.guild_config.unverified_role_id or 0)

            try:
                if verified_role:
                    await interaction.user.add_roles(verified_role, reason="Leakers$ CAPTCHA: Verification Passed")
                if unverified_role and unverified_role in interaction.user.roles:
                    await interaction.user.remove_roles(unverified_role, reason="Leakers$ CAPTCHA: Verification Passed")
            except discord.HTTPException as exc:
                logger.error("Could not modify roles for member %s in %s: %s", user_id, guild_id, exc)
                await interaction.followup.send(
                    "Verification passed, but the bot could not update your roles. "
                    "Please ask a server administrator to check that the bot has **Manage Roles** "
                    "and that its role is above the verified role.",
                    ephemeral=True,
                )
                return

            # Log to SQLite
            await self.bot.db.log_verification(
                guild_id=guild_id,
                user_id=user_id,
                status="SUCCESS",
                attempts=attempts_used,
                style_used=style_used,
            )

            # Audit log to server log channel if configured
            if self.guild_config.log_channel_id:
                log_chan = interaction.guild.get_channel(self.guild_config.log_channel_id)
                if isinstance(log_chan, discord.TextChannel):
                    audit_embed = discord.Embed(
                        title="Member Verified",
                        description=f"{interaction.user.mention} (`{interaction.user.id}`) successfully completed CAPTCHA verification.",
                        color=config.COLOR_SUCCESS,
                    )
                    audit_embed.add_field(name="Style Used", value=f"`{style_used}`", inline=True)
                    audit_embed.add_field(name="Attempts", value=f"`{attempts_used}`", inline=True)
                    audit_embed.set_footer(text="Leakers$ Security Engine")
                    try:
                        await log_chan.send(embed=audit_embed)
                    except Exception as e:
                        logger.warning("Could not dispatch audit log: %s", e)

            success_embed = discord.Embed(
                title="Verification Complete!",
                description=f"Congratulations {interaction.user.mention}! You have been successfully verified and granted access.",
                color=config.COLOR_SUCCESS,
            )
            await interaction.edit_original_response(embed=success_embed, view=None, attachments=[])

        else:
            # Failed attempt
            if attempts_left <= 0:
                # Trigger cooldown
                self.bot.session_manager.trigger_cooldown(guild_id, user_id, self.guild_config.cooldown_seconds)
                await self.bot.db.log_verification(
                    guild_id=guild_id,
                    user_id=user_id,
                    status="FAILED",
                    attempts=self.guild_config.max_attempts,
                    style_used=style_used,
                )
                fail_embed = discord.Embed(
                    title="Verification Failed",
                    description=(
                        f"You have exhausted all attempts.\n"
                        f"A temporary cooldown of **{self.guild_config.cooldown_seconds} seconds** has been applied.\n"
                        f"Please try again later."
                    ),
                    color=config.COLOR_DANGER,
                )
                await interaction.edit_original_response(embed=fail_embed, view=None, attachments=[])
            else:
                # Automatically generate a fresh challenge image on incorrect submission
                captcha_res = await self.bot.captcha_generator.create_captcha(style_name=self.guild_config.captcha_style)

                # Update session with new challenge code and image while retaining remaining attempts
                active_session = self.bot.session_manager.get_session(guild_id, user_id)
                if active_session:
                    active_session.code = captcha_res.code
                    active_session.style_name = captcha_res.style_name
                    active_session.image_bytes = captcha_res.image_bytes

                file = discord.File(io.BytesIO(captcha_res.image_bytes), filename="captcha.png")
                embed = build_challenge_embed(interaction.guild, captcha_res.style_name)

                interaction_view = CaptchaInteractionView(bot=self.bot, guild_config=self.guild_config)
                await interaction.edit_original_response(embed=embed, attachments=[file], view=interaction_view)
                await interaction.followup.send(
                    f"⚠️ **Incorrect answer.** A new CAPTCHA image has been generated ({attempts_left} attempt{'s' if attempts_left != 1 else ''} remaining).\n"
                    f"Click **Submit Code** below to try again.",
                    ephemeral=True,
                )


class CaptchaInteractionView(ui.View):
    """Action bar attached to the active CAPTCHA challenge message."""

    def __init__(self, bot: LeakersCaptchaBot, guild_config: GuildConfig) -> None:
        super().__init__(timeout=guild_config.expiration_seconds)
        self.bot = bot
        self.guild_config = guild_config

    @ui.button(label="Submit Code", style=discord.ButtonStyle.success)
    async def submit_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Opens modal to input the code."""
        modal = CaptchaCodeModal(bot=self.bot, guild_config=self.guild_config)
        await interaction.response.send_modal(modal)

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        """Aborts current session and dismisses view."""
        if interaction.guild:
            self.bot.session_manager.invalidate_session(interaction.guild.id, interaction.user.id)
        cancel_embed = discord.Embed(
            title="Verification Cancelled",
            description="Your verification session was cancelled. You may restart at any time.",
            color=config.COLOR_INFO,
        )
        await interaction.response.edit_message(embed=cancel_embed, view=None, attachments=[])


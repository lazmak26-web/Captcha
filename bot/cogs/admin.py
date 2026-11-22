"""
Leakers$ CAPTCHA - Administration Cog
Provides /setup and /settings slash commands with role and channel validation.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING
import discord
from discord import app_commands
from discord.ext import commands

import config
from bot.views.verify_button_view import VerifyButtonView

if TYPE_CHECKING:
    from bot.client import LeakersCaptchaBot

logger = logging.getLogger("leakers_captcha.cogs.admin")


class SettingsView(discord.ui.View):
    """Interactive view for the /settings command inspired by VoiceMaster buttons."""

    def __init__(self, bot: LeakersCaptchaBot, guild_id: int) -> None:
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        website_emoji = discord.utils.get(bot.emojis, name="world_www") or discord.PartialEmoji(name="world_www", id=1573710974043684915)
        self.add_item(
            discord.ui.Button(
                label="Dashboard",
                style=discord.ButtonStyle.link,
                url=config.WEBSITE_URL,
                emoji=website_emoji,
            )
        )

    @discord.ui.button(
        label="Load Settings",
        style=discord.ButtonStyle.primary,
        emoji=discord.PartialEmoji(name="custom_settings", id=1573719194288132216),
        custom_id="leakers_captcha:reload_settings_btn",
    )
    async def reload_settings_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Reloads and updates the guild settings embed."""
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message("This settings view is for another server.", ephemeral=True)
            return

        cfg = await self.bot.db.get_guild_config(self.guild_id)
        status_embed = discord.Embed(
            title="<:custom_settings:1573719194288132216> Leakers$ CAPTCHA Guild Settings",
            description="Configuration parameters reloaded from database:",
            color=config.COLOR_PRIMARY,
        )

        chan_mention = f"<#{cfg.verification_channel_id}>" if cfg.verification_channel_id else "*Not Configured*"
        role_mention = f"<@&{cfg.verified_role_id}>" if cfg.verified_role_id else "*Not Configured*"
        unver_mention = f"<@&{cfg.unverified_role_id}>" if cfg.unverified_role_id else "*None*"
        log_mention = f"<#{cfg.log_channel_id}>" if cfg.log_channel_id else "*None*"

        status_embed.add_field(name="Verification Channel", value=chan_mention, inline=True)
        status_embed.add_field(name="Verified Role", value=role_mention, inline=True)
        status_embed.add_field(name="Unverified Role", value=unver_mention, inline=True)
        status_embed.add_field(name="Audit Log Channel", value=log_mention, inline=True)
        status_embed.add_field(name="CAPTCHA Style", value=f"`{cfg.captcha_style}`", inline=True)
        status_embed.add_field(name="Expiration Window", value=f"`{cfg.expiration_seconds}s`", inline=True)
        status_embed.add_field(name="Max Attempts Allowed", value=f"`{cfg.max_attempts}`", inline=True)
        status_embed.add_field(name="Penalty Cooldown", value=f"`{cfg.cooldown_seconds}s`", inline=True)
        status_embed.set_footer(text="Run /setup to change channels or roles.")

        await interaction.response.edit_message(embed=status_embed, view=self)


class AdminCog(commands.Cog, name="Admin"):
    """Server management commands for configuring verification channels and rules."""

    def __init__(self, bot: LeakersCaptchaBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="setup",
        description="Configure the verification channel, roles, and post the verification button.",
    )
    @app_commands.describe(
        verification_channel="Channel where the official verification message and button will be placed",
        verified_role="Role to grant to users who successfully complete CAPTCHA",
        unverified_role="Optional role assigned to new members prior to verification",
        log_channel="Optional audit log channel for verification telemetry",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup_verification(
        self,
        interaction: discord.Interaction,
        verification_channel: discord.TextChannel,
        verified_role: discord.Role,
        unverified_role: Optional[discord.Role] = None,
        log_channel: Optional[discord.TextChannel] = None,
    ) -> None:
        """Sets up verification infrastructure in the server."""
        if interaction.guild is None:
            await interaction.response.send_message("This command must be run inside a guild.", ephemeral=True)
            return

        guild = interaction.guild
        bot_member = guild.me

        # Hierarchy permission check: ensure bot's highest role is above verified_role
        if verified_role >= bot_member.top_role:
            await interaction.response.send_message(
                f"❌ Error: The verified role {verified_role.mention} is higher than or equal to my highest role ({bot_member.top_role.mention}). "
                "Please move my bot role higher in Server Settings > Roles.",
                ephemeral=True,
            )
            return

        if unverified_role and unverified_role >= bot_member.top_role:
            await interaction.response.send_message(
                f"❌ Error: The unverified role {unverified_role.mention} is higher than or equal to my highest role. "
                "Please move my bot role higher.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Retrieve or create guild configuration
        cfg = await self.bot.db.get_guild_config(guild.id)
        cfg.verification_channel_id = verification_channel.id
        cfg.verified_role_id = verified_role.id
        cfg.unverified_role_id = unverified_role.id if unverified_role else None
        cfg.log_channel_id = log_channel.id if log_channel else None

        await self.bot.db.save_guild_config(cfg)

        # Dispatch the persistent verification message into the designated channel
        logo_emoji = discord.utils.get(self.bot.emojis, name="leakers_logo") or discord.PartialEmoji(name="leakers_logo", id=1573738656685101286)
        panel_embed = discord.Embed(
            title="<:custom_settings:1573719194288132216> Server Verification Required",
            description=(
                f"Welcome to **{guild.name}**! {logo_emoji}\n\n"
                "To protect our community from automated spam and bot accounts, you must verify your identity.\n\n"
                "**Instructions:**\n"
                "1. Click the green **Verify** button below.\n"
                "2. Read the characters displayed in the security image.\n"
                "3. Click **Submit Code** and enter the characters to receive your role.\n\n"
                "*Challenges expire quickly. Enter the code before the timer runs out.*"
            ),
            color=config.COLOR_PRIMARY,
        )
        if guild.icon:
            panel_embed.set_thumbnail(url=guild.icon.url)
        panel_embed.set_footer(text="Secured by Leakers$ CAPTCHA Engine")

        try:
            view = VerifyButtonView(self.bot)
            await verification_channel.send(embed=panel_embed, view=view)
        except discord.Forbidden:
            await interaction.followup.send(
                f"Configuration saved, but I lack permission to send messages in {verification_channel.mention}!",
                ephemeral=True,
            )
            return

        response_embed = discord.Embed(
            title="✅ Leakers$ CAPTCHA Setup Complete",
            description=f"Verification panel has been posted to {verification_channel.mention}!",
            color=config.COLOR_SUCCESS,
        )
        response_embed.add_field(name="Verification Channel", value=verification_channel.mention, inline=True)
        response_embed.add_field(name="Verified Role", value=verified_role.mention, inline=True)
        response_embed.add_field(
            name="Unverified Role",
            value=unverified_role.mention if unverified_role else "*None*",
            inline=True,
        )
        response_embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "*None*",
            inline=True,
        )
        response_embed.add_field(name="Active CAPTCHA Style", value=f"`{cfg.captcha_style}`", inline=True)
        response_embed.add_field(name="Expiration Timeout", value=f"`{cfg.expiration_seconds}s`", inline=True)

        await interaction.followup.send(embed=response_embed, ephemeral=True)

    @app_commands.command(
        name="settings",
        description="View or adjust verification parameters (style, timeout, attempts, cooldown).",
    )
    @app_commands.describe(
        style="Visual distortion style for CAPTCHA images",
        expiration_seconds="Session lifetime in seconds (30-600)",
        max_attempts="Maximum attempts allowed before cooldown (1-10)",
        cooldown_seconds="Penalty cooldown duration in seconds (30-3600)",
    )
    @app_commands.choices(
        style=[
            app_commands.Choice(name=s, value=s) for s in config.ALL_STYLE_CHOICES
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def settings(
        self,
        interaction: discord.Interaction,
        style: Optional[app_commands.Choice[str]] = None,
        expiration_seconds: Optional[app_commands.Range[int, 30, 600]] = None,
        max_attempts: Optional[app_commands.Range[int, 1, 10]] = None,
        cooldown_seconds: Optional[app_commands.Range[int, 30, 3600]] = None,
    ) -> None:
        """Inspects or updates guild verification settings."""
        if interaction.guild is None:
            await interaction.response.send_message("This command must be run inside a guild.", ephemeral=True)
            return

        cfg = await self.bot.db.get_guild_config(interaction.guild.id)
        updates: list[str] = []

        if style is not None:
            cfg.captcha_style = style.value
            updates.append(f"• **CAPTCHA Style**: changed to `{style.value}`")

        if expiration_seconds is not None:
            cfg.expiration_seconds = int(expiration_seconds)
            updates.append(f"• **Expiration**: changed to `{expiration_seconds}s`")

        if max_attempts is not None:
            cfg.max_attempts = int(max_attempts)
            updates.append(f"• **Max Attempts**: changed to `{max_attempts}`")

        if cooldown_seconds is not None:
            cfg.cooldown_seconds = int(cooldown_seconds)
            updates.append(f"• **Cooldown**: changed to `{cooldown_seconds}s`")

        if updates:
            await self.bot.db.save_guild_config(cfg)

        status_embed = discord.Embed(
            title="<:custom_settings:1573719194288132216> Leakers$ CAPTCHA Guild Settings",
            description="\n".join(updates) if updates else "Current configuration parameters:",
            color=config.COLOR_PRIMARY,
        )

        chan_mention = f"<#{cfg.verification_channel_id}>" if cfg.verification_channel_id else "*Not Configured*"
        role_mention = f"<@&{cfg.verified_role_id}>" if cfg.verified_role_id else "*Not Configured*"
        unver_mention = f"<@&{cfg.unverified_role_id}>" if cfg.unverified_role_id else "*None*"
        log_mention = f"<#{cfg.log_channel_id}>" if cfg.log_channel_id else "*None*"

        status_embed.add_field(name="Verification Channel", value=chan_mention, inline=True)
        status_embed.add_field(name="Verified Role", value=role_mention, inline=True)
        status_embed.add_field(name="Unverified Role", value=unver_mention, inline=True)
        status_embed.add_field(name="Audit Log Channel", value=log_mention, inline=True)
        status_embed.add_field(name="CAPTCHA Style", value=f"`{cfg.captcha_style}`", inline=True)
        status_embed.add_field(name="Expiration Window", value=f"`{cfg.expiration_seconds}s`", inline=True)
        status_embed.add_field(name="Max Attempts Allowed", value=f"`{cfg.max_attempts}`", inline=True)
        status_embed.add_field(name="Penalty Cooldown", value=f"`{cfg.cooldown_seconds}s`", inline=True)
        status_embed.set_footer(text="Run /setup to change channels or roles.")

        view = SettingsView(self.bot, interaction.guild.id)
        await interaction.response.send_message(embed=status_embed, view=view, ephemeral=True)


async def setup(bot: LeakersCaptchaBot) -> None:
    """Extension cog setup entry point."""
    await bot.add_cog(AdminCog(bot))


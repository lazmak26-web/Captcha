"""
Leakers$ CAPTCHA - Slash Commands & Architecture Test Suite
Validates cog loading, application command registration, parameter typing, and views.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
import discord

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bot.client import LeakersCaptchaBot
from bot.views.verify_button_view import VerifyButtonView
from bot.views.captcha_modal_view import CaptchaInteractionView, CaptchaCodeModal
from database import GuildConfig


class TestSlashCommandsAndArchitecture(unittest.IsolatedAsyncioTestCase):
    """Verifies that Discord application commands, cogs, and views are compliant."""

    async def asyncSetUp(self) -> None:
        self.bot = LeakersCaptchaBot()
        cogs = [
            "bot.cogs.verification",
            "bot.cogs.admin",
            "bot.cogs.stats",
        ]
        for cog in cogs:
            await self.bot.load_extension(cog)

    def test_all_five_slash_commands_registered(self) -> None:
        """Verifies that all 5 required slash commands exist on the bot's command tree."""
        commands = self.bot.tree.get_commands()
        command_map = {cmd.name: cmd for cmd in commands}

        required_commands = ["setup", "verify", "settings", "stats", "help"]
        for cmd_name in required_commands:
            self.assertIn(
                cmd_name,
                command_map,
                f"Required slash command '/{cmd_name}' is not registered on tree",
            )

    def test_setup_command_parameters(self) -> None:
        """Verifies /setup parameters and admin permission guards."""
        cmd = self.bot.tree.get_command("setup")
        self.assertIsNotNone(cmd)
        param_names = [p.name for p in cmd.parameters]
        self.assertIn("verification_channel", param_names)
        self.assertIn("verified_role", param_names)
        self.assertIn("unverified_role", param_names)
        self.assertIn("log_channel", param_names)
        # Check manage_guild permission
        self.assertTrue(cmd.default_permissions.manage_guild)

    def test_settings_command_parameters_and_choices(self) -> None:
        """Verifies /settings parameters and style choices."""
        cmd = self.bot.tree.get_command("settings")
        self.assertIsNotNone(cmd)
        param_names = [p.name for p in cmd.parameters]
        self.assertIn("style", param_names)
        self.assertIn("expiration_seconds", param_names)
        self.assertIn("max_attempts", param_names)
        self.assertIn("cooldown_seconds", param_names)

        # Verify style parameter has choices defined
        style_param = next(p for p in cmd.parameters if p.name == "style")
        choice_values = [c.value for c in style_param.choices]
        self.assertIn("Collage", choice_values)
        self.assertIn("Random", choice_values)
        self.assertIn("Strippy", choice_values)

    def test_persistent_verify_button_view(self) -> None:
        """Verifies that the persistent verification view has timeout=None and correct custom_id."""
        view = VerifyButtonView(self.bot)
        self.assertIsNone(view.timeout)
        buttons = [item for item in view.children if isinstance(item, discord.ui.Button)]
        self.assertTrue(any(b.custom_id == "leakers_captcha:verify_btn" for b in buttons))

    def test_captcha_interaction_view_components(self) -> None:
        """Verifies that the interaction view includes submit and cancel buttons."""
        dummy_cfg = GuildConfig(guild_id=1, expiration_seconds=120)
        view = CaptchaInteractionView(self.bot, dummy_cfg)
        self.assertEqual(view.timeout, 120)

        buttons = [item for item in view.children if isinstance(item, discord.ui.Button)]
        labels = [b.label for b in buttons]
        self.assertIn("Submit Code", labels)
        self.assertIn("Cancel", labels)
        self.assertNotIn("New Image", labels)


def main() -> int:
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSlashCommandsAndArchitecture)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())


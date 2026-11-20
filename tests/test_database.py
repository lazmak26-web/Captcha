"""
Leakers$ CAPTCHA - Database Unit Tests
Validates asynchronous SQLite schema initialization, CRUD operations, and telemetry.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import DatabaseManager, GuildConfig

TEST_DB_FILE = "tests/test_run.db"


class TestDatabaseManager(unittest.IsolatedAsyncioTestCase):
    """Verifies SQLite persistence and analytical query aggregates."""

    async def asyncSetUp(self) -> None:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
        self.db = DatabaseManager(TEST_DB_FILE)
        await self.db.initialize()

    async def asyncTearDown(self) -> None:
        if os.path.exists(TEST_DB_FILE):
            try:
                os.remove(TEST_DB_FILE)
            except Exception:
                pass

    async def test_guild_config_defaults(self) -> None:
        """New guilds return default configuration."""
        cfg = await self.db.get_guild_config(987654321)
        self.assertEqual(cfg.guild_id, 987654321)
        self.assertIsNone(cfg.verification_channel_id)
        self.assertIsNone(cfg.verified_role_id)
        self.assertFalse(cfg.is_configured)

    async def test_guild_config_upsert(self) -> None:
        """Saving full guild config persists and is retrieved accurately."""
        cfg = GuildConfig(
            guild_id=123456789,
            verification_channel_id=11111,
            verified_role_id=22222,
            unverified_role_id=33333,
            log_channel_id=44444,
            captcha_style="Snow",
            expiration_seconds=240,
            max_attempts=5,
            cooldown_seconds=600,
        )
        await self.db.save_guild_config(cfg)

        loaded = await self.db.get_guild_config(123456789)
        self.assertTrue(loaded.is_configured)
        self.assertEqual(loaded.verification_channel_id, 11111)
        self.assertEqual(loaded.verified_role_id, 22222)
        self.assertEqual(loaded.unverified_role_id, 33333)
        self.assertEqual(loaded.log_channel_id, 44444)
        self.assertEqual(loaded.captcha_style, "Snow")
        self.assertEqual(loaded.expiration_seconds, 240)
        self.assertEqual(loaded.max_attempts, 5)
        self.assertEqual(loaded.cooldown_seconds, 600)

    async def test_update_guild_field(self) -> None:
        """Partial updates modify target field without overwriting others."""
        await self.db.update_guild_field(555, "captcha_style", "SpiderWeb")
        await self.db.update_guild_field(555, "max_attempts", 4)

        loaded = await self.db.get_guild_config(555)
        self.assertEqual(loaded.captcha_style, "SpiderWeb")
        self.assertEqual(loaded.max_attempts, 4)

    async def test_invalid_field_update_raises(self) -> None:
        """Passing an unrecognized field raises ValueError."""
        with self.assertRaises(ValueError):
            await self.db.update_guild_field(555, "malicious_field", "value")

    async def test_verification_logs_and_stats(self) -> None:
        """Telemetry records are recorded and aggregated properly."""
        guild_id = 999
        await self.db.log_verification(guild_id, 101, "SUCCESS", 1, "Collage")
        await self.db.log_verification(guild_id, 102, "SUCCESS", 2, "Snow")
        await self.db.log_verification(guild_id, 103, "FAILED", 3, "Corrosion")
        await self.db.log_verification(guild_id, 104, "EXPIRED", 1, "Cut")

        stats = await self.db.get_guild_stats(guild_id)
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["passed"], 2)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["expired"], 1)


def main() -> int:
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatabaseManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())


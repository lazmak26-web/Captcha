"""
Leakers$ CAPTCHA - Database Manager
Async SQLite storage engine for guild configurations and verification telemetry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional
import aiosqlite

import config

logger = logging.getLogger("leakers_captcha.database")


@dataclass
class GuildConfig:
    """Represents configuration settings for a Discord guild."""
    guild_id: int
    verification_channel_id: Optional[int] = None
    verified_role_id: Optional[int] = None
    unverified_role_id: Optional[int] = None
    log_channel_id: Optional[int] = None
    captcha_style: str = config.DEFAULT_CAPTCHA_STYLE
    expiration_seconds: int = config.DEFAULT_EXPIRATION_SECONDS
    max_attempts: int = config.DEFAULT_MAX_ATTEMPTS
    cooldown_seconds: int = config.DEFAULT_COOLDOWN_SECONDS

    @property
    def is_configured(self) -> bool:
        """Determines if the minimum required settings are configured."""
        return (
            self.verification_channel_id is not None
            and self.verified_role_id is not None
        )


class DatabaseManager:
    """Manages asynchronous SQLite database connections and queries."""

    def __init__(self, db_path: str = config.DATABASE_PATH) -> None:
        self.db_path = db_path

    async def initialize(self) -> None:
        """Creates the required tables and indexes if they do not exist."""
        logger.info("Initializing database schema at: %s", self.db_path)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA foreign_keys = ON;")

            # Guild configurations table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    verification_channel_id INTEGER,
                    verified_role_id INTEGER,
                    unverified_role_id INTEGER,
                    log_channel_id INTEGER,
                    captcha_style TEXT NOT NULL DEFAULT 'MarketShapes',
                    expiration_seconds INTEGER NOT NULL DEFAULT 180,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    cooldown_seconds INTEGER NOT NULL DEFAULT 300,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Verification history and analytics table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS verification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    style_used TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Indexes for analytical queries
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_logs_guild_status 
                ON verification_logs (guild_id, status);
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_logs_created 
                ON verification_logs (created_at);
                """
            )

            await db.commit()
        logger.info("Database schema initialized successfully.")

    async def get_guild_config(self, guild_id: int) -> GuildConfig:
        """Fetches the configuration for a given guild or returns defaults."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT guild_id, verification_channel_id, verified_role_id,
                       unverified_role_id, log_channel_id, captcha_style,
                       expiration_seconds, max_attempts, cooldown_seconds
                FROM guild_settings
                WHERE guild_id = ?;
                """,
                (guild_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return GuildConfig(guild_id=guild_id)

            return GuildConfig(
                guild_id=row["guild_id"],
                verification_channel_id=row["verification_channel_id"],
                verified_role_id=row["verified_role_id"],
                unverified_role_id=row["unverified_role_id"],
                log_channel_id=row["log_channel_id"],
                captcha_style=row["captcha_style"],
                expiration_seconds=row["expiration_seconds"],
                max_attempts=row["max_attempts"],
                cooldown_seconds=row["cooldown_seconds"],
            )

    async def save_guild_config(self, cfg: GuildConfig) -> None:
        """Upserts a complete guild configuration record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO guild_settings (
                    guild_id, verification_channel_id, verified_role_id,
                    unverified_role_id, log_channel_id, captcha_style,
                    expiration_seconds, max_attempts, cooldown_seconds,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(guild_id) DO UPDATE SET
                    verification_channel_id = excluded.verification_channel_id,
                    verified_role_id = excluded.verified_role_id,
                    unverified_role_id = excluded.unverified_role_id,
                    log_channel_id = excluded.log_channel_id,
                    captcha_style = excluded.captcha_style,
                    expiration_seconds = excluded.expiration_seconds,
                    max_attempts = excluded.max_attempts,
                    cooldown_seconds = excluded.cooldown_seconds,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    cfg.guild_id,
                    cfg.verification_channel_id,
                    cfg.verified_role_id,
                    cfg.unverified_role_id,
                    cfg.log_channel_id,
                    cfg.captcha_style,
                    cfg.expiration_seconds,
                    cfg.max_attempts,
                    cfg.cooldown_seconds,
                ),
            )
            await db.commit()

    async def update_guild_field(self, guild_id: int, field_name: str, value: Any) -> None:
        """Safely updates a single field in the guild configuration."""
        valid_fields = {
            "verification_channel_id",
            "verified_role_id",
            "unverified_role_id",
            "log_channel_id",
            "captcha_style",
            "expiration_seconds",
            "max_attempts",
            "cooldown_seconds",
        }
        if field_name not in valid_fields:
            raise ValueError(f"Invalid field name: {field_name}")

        async with aiosqlite.connect(self.db_path) as db:
            # First ensure the row exists
            await db.execute(
                """
                INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?);
                """,
                (guild_id,),
            )
            query = f"UPDATE guild_settings SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?;"
            await db.execute(query, (value, guild_id))
            await db.commit()

    async def log_verification(
        self,
        guild_id: int,
        user_id: int,
        status: str,
        attempts: int,
        style_used: str,
    ) -> None:
        """Inserts an audit record for a verification attempt."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO verification_logs (guild_id, user_id, status, attempts, style_used)
                VALUES (?, ?, ?, ?, ?);
                """,
                (guild_id, user_id, status, attempts, style_used),
            )
            await db.commit()

    async def get_guild_stats(self, guild_id: int) -> dict[str, int]:
        """Calculates verification telemetry counts for a given guild."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as expired
                FROM verification_logs
                WHERE guild_id = ?;
                """,
                (guild_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return {"total": 0, "passed": 0, "failed": 0, "expired": 0}

            return {
                "total": int(row[0] or 0),
                "passed": int(row[1] or 0),
                "failed": int(row[2] or 0),
                "expired": int(row[3] or 0),
            }


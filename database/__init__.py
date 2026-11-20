"""
Leakers$ CAPTCHA - Database Package
Exposes DatabaseManager for managing persistent SQLite operations.
"""

from .db_manager import DatabaseManager, GuildConfig

__all__ = ["DatabaseManager", "GuildConfig"]


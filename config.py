"""
Leakers$ CAPTCHA - Global Configuration Module
Loads environment variables and exposes typed application constants.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base directories
BASE_DIR: Final[Path] = Path(__file__).resolve().parent

# Authentication
BOT_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN", "").strip()

# Database Configuration
DATABASE_PATH: Final[str] = os.getenv("DATABASE_PATH", "leakers_captcha.db").strip()

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO").upper().strip()

# Visual CAPTCHA Supported Styles
SUPPORTED_STYLES: Final[tuple[str, ...]] = (
    "MarketShapes",
    "Collage",
    "Snow",
    "Corrosion",
    "SpiderWeb",
    "CrossShadow",
    "CrossShadow2",
    "Cut",
    "Darts",
    "Distortion",
    "Split",
    "Split2",
    "Stitch",
    "Strippy",
)

# Style choices including Random
ALL_STYLE_CHOICES: Final[tuple[str, ...]] = SUPPORTED_STYLES + ("Random",)

# CAPTCHA Generation Constants
DEFAULT_CAPTCHA_STYLE: Final[str] = os.getenv("DEFAULT_CAPTCHA_STYLE", "MarketShapes").strip()
DEFAULT_EXPIRATION_SECONDS: Final[int] = int(os.getenv("DEFAULT_EXPIRATION_SECONDS", "180"))
DEFAULT_MAX_ATTEMPTS: Final[int] = int(os.getenv("DEFAULT_MAX_ATTEMPTS", "3"))
DEFAULT_COOLDOWN_SECONDS: Final[int] = int(os.getenv("DEFAULT_COOLDOWN_SECONDS", "300"))
CAPTCHA_LENGTH: Final[int] = int(os.getenv("CAPTCHA_LENGTH", "6"))

# Image Dimensions
CAPTCHA_IMAGE_WIDTH: Final[int] = 340
CAPTCHA_IMAGE_HEIGHT: Final[int] = 120

# Character Set for Challenge Generation (avoiding ambiguous characters like 0, O, 1, I, l)
CHARSET: Final[str] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Official Website URL
WEBSITE_URL: Final[str] = os.getenv("WEBSITE_URL", "https://leak3rs.xyz/").strip()

# Allowed Channels where bot commands and interactions are active
ALLOWED_CHANNEL_IDS: Final[tuple[int, ...]] = (
    1572920165740585110,  # #verify
    1573496629250621520,  # #verify-logs
)

# Discord UI Theme Colors (Hex values)
COLOR_PRIMARY: Final[int] = 0x1A1A1A    # Dark Grey (#1A1A1A)
COLOR_SUCCESS: Final[int] = 0x57F287    # Green
COLOR_DANGER: Final[int] = 0xED4245     # Red
COLOR_WARNING: Final[int] = 0xFEE75C    # Yellow
COLOR_INFO: Final[int] = 0x3498DB       # Blue


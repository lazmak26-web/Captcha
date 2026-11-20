"""
Leakers$ CAPTCHA - Main Application Entrypoint
Initializes structured logging, configuration validation, diagnostic self-tests,
and boots the Discord client.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import config
from database import DatabaseManager
from captcha import CaptchaGenerator
from captcha.styles import STYLE_REGISTRY
from bot.client import LeakersCaptchaBot


def setup_logging(verbose: bool = False) -> None:
    """Configures structured console logging with timestamping."""
    log_format = "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    level = logging.DEBUG if verbose else getattr(logging, config.LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Silence excessively verbose discord gateway heartbeat logs
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.INFO)


async def run_boot_diagnostics(verbose: bool = False) -> bool:
    """
    Performs comprehensive dry-run boot diagnostics:
    - Validates SQLite database connection and schema.
    - Validates all 13 visual CAPTCHA styles and generators.
    - Instantiates LeakersCaptchaBot and verifies cog imports and view bindings.
    """
    logger = logging.getLogger("leakers_captcha.boot_check")
    logger.info("Executing comprehensive Leakers$ CAPTCHA boot diagnostics...")

    # 1. Database validation
    logger.info("[1/4] Validating database initialization and schema...")
    db = DatabaseManager(config.DATABASE_PATH)
    await db.initialize()
    logger.info("      Database initialized and schema verified.")

    # 2. CAPTCHA Engine validation (all 13 styles)
    logger.info("[2/4] Validating all 13 visual CAPTCHA styles...")
    generator = CaptchaGenerator()
    for style_name in STYLE_REGISTRY:
        res = await generator.create_captcha(style_name=style_name, length=6)
        if len(res.image_bytes) < 500:
            logger.error("Style %s produced invalid or empty image output!", style_name)
            return False
        if verbose:
            logger.debug("      Style '%s': OK (%d bytes, code: %s)", style_name, len(res.image_bytes), res.code)
    logger.info("      All %d visual CAPTCHA styles generated valid images.", len(STYLE_REGISTRY))

    # 3. Bot client & Cogs validation
    logger.info("[3/4] Validating bot client and extension cogs...")
    bot = LeakersCaptchaBot()
    cogs = [
        "bot.cogs.verification",
        "bot.cogs.admin",
        "bot.cogs.stats",
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info("      Cog '%s': Loaded successfully.", cog)
        except Exception as exc:
            logger.error("      Failed loading cog '%s': %s", cog, exc)
            return False

    # 4. Command tree validation
    logger.info("[4/4] Validating slash command tree definition...")
    commands = bot.tree.get_commands()
    command_names = [cmd.name for cmd in commands]
    logger.info("      Registered application commands: %s", ", ".join(f"/{c}" for c in command_names))

    required_commands = {"setup", "verify", "settings", "stats", "help"}
    missing = required_commands - set(command_names)
    if missing:
        logger.error("Missing required slash commands: %s", missing)
        return False

    logger.info("All boot diagnostics passed successfully (0 errors).")
    return True


def main() -> None:
    """Validates runtime configuration and starts the bot or diagnostic test."""
    parser = argparse.ArgumentParser(description="Leakers$ CAPTCHA Discord Bot")
    parser.add_argument(
        "--dry-run",
        "--check",
        "--test",
        dest="dry_run",
        action="store_true",
        help="Run comprehensive boot self-checks and exit without connecting to Discord.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger("leakers_captcha.main")

    # If explicit dry-run / check requested
    if args.dry_run:
        logger.info("Dry-run / boot check mode enabled.")
        success = asyncio.run(run_boot_diagnostics(verbose=args.verbose))
        sys.exit(0 if success else 1)

    # Check for Discord Bot Token
    token = config.BOT_TOKEN
    is_placeholder = not token or token == "your_bot_token_here"

    if is_placeholder:
        logger.warning(
            "No valid DISCORD_TOKEN found in environment or .env file. "
            "Executing boot diagnostics & self-test dry-run..."
        )
        success = asyncio.run(run_boot_diagnostics(verbose=args.verbose))
        if success:
            logger.info("=" * 70)
            logger.info("DIAGNOSTIC BOOT CHECK PASSED!")
            logger.info("To start the live Discord bot, set your DISCORD_TOKEN in .env and rerun:")
            logger.info("    python main.py")
            logger.info("=" * 70)
            sys.exit(0)
        else:
            logger.critical("Boot check encountered errors during self-test.")
            sys.exit(1)

    # Token exists: boot live Discord client
    logger.info("Starting Leakers$ CAPTCHA Bot in live mode...")
    bot = LeakersCaptchaBot()

    try:
        bot.run(token, log_handler=None)
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user. Shutting down gracefully...")
    except Exception as exc:
        logger.critical("Fatal error occurred during bot execution: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Leakers$ CAPTCHA - Unified Generator Engine
Coordinates cryptographically secure code generation, style resolution, and rendering.
"""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass

import config
from .styles import BaseCaptchaStyle, get_style


@dataclass(frozen=True)
class CaptchaResult:
    """Represents a generated CAPTCHA challenge output."""
    code: str
    style_name: str
    image_bytes: bytes


class CaptchaGenerator:
    """Orchestrates random code generation and image synthesis."""

    def __init__(self, charset: str = config.CHARSET) -> None:
        self.charset = charset

    def generate_random_code(self, length: int = config.CAPTCHA_LENGTH) -> str:
        """
        Generates a cryptographically secure random alphanumeric string
        excluding easily confused characters (such as 0/O, 1/I).
        """
        return "".join(secrets.choice(self.charset) for _ in range(length))

    def _render_sync(
        self,
        code: str | None,
        style_name: str,
        width: int,
        height: int,
    ) -> CaptchaResult:
        """Synchronously renders the image and encodes to bytes."""
        style: BaseCaptchaStyle = get_style(style_name)
        if hasattr(style, "generate_challenge") and (code is None or style.name == "MarketShapes"):
            img, gen_code = style.generate_challenge()
            img_bytes = style.to_bytes(img)
            return CaptchaResult(
                code=gen_code,
                style_name=style.name,
                image_bytes=img_bytes,
            )

        final_code = code or self.generate_random_code()
        img = style.generate(final_code, width=width, height=height)
        img_bytes = style.to_bytes(img)
        return CaptchaResult(
            code=final_code,
            style_name=style.name,
            image_bytes=img_bytes,
        )

    async def create_captcha(
        self,
        style_name: str = config.DEFAULT_CAPTCHA_STYLE,
        length: int = config.CAPTCHA_LENGTH,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
        code: str | None = None,
    ) -> CaptchaResult:
        """
        Asynchronously creates a new CAPTCHA challenge offloaded to the
        default threadpool executor to avoid blocking the Discord gateway loop.
        """
        challenge_code = code if code is not None else (None if style_name == "MarketShapes" else self.generate_random_code(length))
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._render_sync,
            challenge_code,
            style_name,
            width,
            height,
        )


"""
Leakers$ CAPTCHA - Snow Style
Simulates falling snow crystals, frosty particles, and icy cool tones.
"""

from __future__ import annotations

import math
import random
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseCaptchaStyle
import config


class SnowStyle(BaseCaptchaStyle):
    """Snow Style: Blizzard particles and frosty crystalline noise."""

    name: str = "Snow"

    def _draw_snowflake(self, draw: ImageDraw.ImageDraw, x: int, y: int, radius: int) -> None:
        """Draws a 6-branched snowflake crystal."""
        color = (255, 255, 255, random.randint(180, 240))
        for i in range(3):
            angle = i * (math.pi / 3)
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)
            draw.line([(x - dx, y - dy), (x + dx, y + dy)], fill=color, width=1)

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Cool icy blue-gray background
        img = Image.new("RGBA", (width, height), (220, 235, 248, 255))
        draw = ImageDraw.Draw(img)

        # Base characters
        base_chars = self.render_characters_individually(text, width, height, font_size=50, max_angle=20)
        img.paste(base_chars, (0, 0), base_chars)

        # Draw dense snowfall dots
        for _ in range(250):
            sx = random.randint(0, width)
            sy = random.randint(0, height)
            sr = random.randint(1, 3)
            draw.ellipse([(sx - sr, sy - sr), (sx + sr, sy + sr)], fill=(255, 255, 255, random.randint(150, 255)))

        # Draw geometric snowflakes
        for _ in range(12):
            fx = random.randint(0, width)
            fy = random.randint(0, height)
            fr = random.randint(5, 11)
            self._draw_snowflake(draw, fx, fy, fr)

        # Frost drift wind lines
        for _ in range(6):
            y_pos = random.randint(10, height - 10)
            draw.line([(0, y_pos), (width, y_pos + random.randint(-15, 15))], fill=(240, 250, 255, 160), width=random.randint(1, 2))

        return img


"""
Leakers$ CAPTCHA - Darts Style
Simulates dart trajectories, flight trails, and target concentric rings.
"""

from __future__ import annotations

import math
import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class DartsStyle(BaseCaptchaStyle):
    """Darts Style: Target bullseye rings and projectile dart flight lines."""

    name: str = "Darts"

    def _draw_dart(self, draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
        """Draws an arrow dart with fletchings and sharp tip."""
        draw.line([start, end], fill=(237, 66, 69, 220), width=2)

        # Arrowhead at end
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_len = 8
        a1 = angle + math.pi * 0.8
        a2 = angle - math.pi * 0.8
        p1 = (end[0] + arrow_len * math.cos(a1), end[1] + arrow_len * math.sin(a1))
        p2 = (end[0] + arrow_len * math.cos(a2), end[1] + arrow_len * math.sin(a2))
        draw.polygon([end, p1, p2], fill=(237, 66, 69, 240))

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (246, 248, 250, 255))
        draw = ImageDraw.Draw(img)

        # Draw concentric target rings in background
        target_centers = [(width // 5, height // 2), (4 * width // 5, height // 2)]
        for tx, ty in target_centers:
            for radius in (15, 30, 45):
                draw.ellipse([(tx - radius, ty - radius), (tx + radius, ty + radius)], outline=(210, 218, 230, 160), width=1)

        # Render characters
        chars = self.render_characters_individually(text, width, height, font_size=52, max_angle=18)
        img.paste(chars, (0, 0), chars)

        # Draw projectile dart vectors piercing through the text
        for _ in range(5):
            sx = random.randint(0, width // 2)
            sy = random.randint(0, height)
            ex = sx + random.randint(50, 120)
            ey = sy + random.randint(-30, 30)
            self._draw_dart(draw, (sx, sy), (ex, ey))

        # Impact impact points
        for _ in range(25):
            ix = random.randint(0, width)
            iy = random.randint(0, height)
            draw.ellipse([(ix - 2, iy - 2), (ix + 2, iy + 2)], fill=(237, 66, 69, 180))

        return img


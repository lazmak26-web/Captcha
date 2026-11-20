"""
Leakers$ CAPTCHA - Stitch Style
Simulates embroidered seams, zigzag thread lines, and cross-stitch patterns.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class StitchStyle(BaseCaptchaStyle):
    """Stitch Style: Needlework stitches and interwoven thread sutures."""

    name: str = "Stitch"

    def _draw_zigzag_stitch(self, draw: ImageDraw.ImageDraw, y_level: int, width: int) -> None:
        """Draws a zigzag sewing machine stitch line across the image."""
        step = 10
        amplitude = 6
        points = []
        up = True
        stitch_color = (random.randint(60, 100), random.randint(70, 120), random.randint(180, 240), 220)

        for x in range(0, width + step, step):
            y = y_level + (-amplitude if up else amplitude) + random.randint(-1, 1)
            points.append((x, y))
            up = not up

        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=stitch_color, width=2)
            # Needle puncture hole
            px, py = points[i]
            draw.ellipse([(px - 1, py - 1), (px + 1, py + 1)], fill=(40, 40, 50, 200))

    def _draw_cross_stitch(self, draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 5) -> None:
        """Draws a single X stitch."""
        color = (237, 66, 69, 190)
        draw.line([(x - size, y - size), (x + size, y + size)], fill=color, width=2)
        draw.line([(x - size, y + size), (x + size, y - size)], fill=color, width=2)

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Fabric textured background (subtle light linen)
        img = Image.new("RGBA", (width, height), (242, 240, 235, 255))
        draw = ImageDraw.Draw(img)

        # Draw linen cross-threads
        for y in range(0, height, 8):
            draw.line([(0, y), (width, y)], fill=(230, 226, 220, 120), width=1)
        for x in range(0, width, 8):
            draw.line([(x, 0), (x, height)], fill=(230, 226, 220, 120), width=1)

        # Characters
        chars = self.render_characters_individually(text, width, height, font_size=52, max_angle=14)
        img.paste(chars, (0, 0), chars)

        # Zigzag stitch traversing through text
        self._draw_zigzag_stitch(draw, height // 2 + random.randint(-10, 10), width)

        # Cross stitches along borders
        for x in range(15, width - 15, 25):
            self._draw_cross_stitch(draw, x, 12)
            self._draw_cross_stitch(draw, x, height - 12)

        return img


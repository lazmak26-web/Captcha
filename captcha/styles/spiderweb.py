"""
Leakers$ CAPTCHA - SpiderWeb Style
Draws interwoven radial filaments and concentric spiderweb geometry.
"""

from __future__ import annotations

import math
import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class SpiderWebStyle(BaseCaptchaStyle):
    """SpiderWeb Style: Filament strands, radial nodes, and connecting web arcs."""

    name: str = "SpiderWeb"

    def _draw_web(self, draw: ImageDraw.ImageDraw, center_x: int, center_y: int, max_radius: int) -> None:
        """Constructs a radial spiderweb centered around given point."""
        spokes = 12
        rings = 6
        web_color = (random.randint(90, 140), random.randint(90, 140), random.randint(110, 160), 160)

        # Draw radiating spokes
        angles = [i * (2 * math.pi / spokes) for i in range(spokes)]
        for angle in angles:
            ex = center_x + int(max_radius * math.cos(angle))
            ey = center_y + int(max_radius * math.sin(angle))
            draw.line([(center_x, center_y), (ex, ey)], fill=web_color, width=1)

        # Draw connecting concentric rings
        for r_step in range(1, rings + 1):
            r = int((r_step / rings) * max_radius)
            pts = []
            for angle in angles:
                px = center_x + int(r * math.cos(angle)) + random.randint(-2, 2)
                py = center_y + int(r * math.sin(angle)) + random.randint(-2, 2)
                pts.append((px, py))
            # Close ring loop
            pts.append(pts[0])
            draw.line(pts, fill=web_color, width=1)

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Misty grayish-blue canvas
        img = Image.new("RGBA", (width, height), (240, 242, 245, 255))
        draw = ImageDraw.Draw(img)

        # Web behind text
        self._draw_web(draw, center_x=width // 4, center_y=height // 3, max_radius=85)

        # Render characters
        chars = self.render_characters_individually(text, width, height, font_size=52, max_angle=15)
        img.paste(chars, (0, 0), chars)

        # Web on top of text
        self._draw_web(draw, center_x=3 * width // 4, center_y=2 * height // 3, max_radius=95)

        # Scattered dew drops on web strings
        for _ in range(40):
            dx = random.randint(0, width)
            dy = random.randint(0, height)
            draw.ellipse([(dx - 1, dy - 1), (dx + 1, dy + 1)], fill=(255, 255, 255, 210))

        return img


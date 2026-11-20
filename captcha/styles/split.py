"""
Leakers$ CAPTCHA - Split Style
Bifurcates canvas across the horizontal median with divergent shifts.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class SplitStyle(BaseCaptchaStyle):
    """Split Style: Horizontal midline fracture with opposing lateral displacement."""

    name: str = "Split"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        base = self.render_characters_individually(text, width, height, font_size=52, max_angle=12)
        out = Image.new("RGBA", (width, height), (245, 246, 250, 255))

        mid_y = height // 2 + random.randint(-4, 4)
        top_half = base.crop((0, 0, width, mid_y))
        bottom_half = base.crop((0, mid_y, width, height))

        # Opposing horizontal offsets
        shift = random.randint(7, 13)
        out.paste(top_half, (-shift, 0))
        out.paste(bottom_half, (shift, mid_y))

        draw = ImageDraw.Draw(out)
        # Midline fracture rupture
        draw.line([(0, mid_y), (width, mid_y)], fill=(88, 101, 242, 180), width=2)

        # Subtle noise dots
        self.draw_noise_dots(draw, width, height, count=50)
        return out


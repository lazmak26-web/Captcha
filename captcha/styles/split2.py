"""
Leakers$ CAPTCHA - Split2 Style
Four-quadrant tectonic fracture with diagonal opposing displacements.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class Split2Style(BaseCaptchaStyle):
    """Split2 Style: Quad-split separating canvas into four distinct shifting segments."""

    name: str = "Split2"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        base = self.render_characters_individually(text, width, height, font_size=52, max_angle=10)
        out = Image.new("RGBA", (width, height), (242, 245, 248, 255))

        mid_x = width // 2 + random.randint(-10, 10)
        mid_y = height // 2 + random.randint(-4, 4)

        # 4 Quadrants
        q1 = base.crop((0, 0, mid_x, mid_y))           # Top-left
        q2 = base.crop((mid_x, 0, width, mid_y))       # Top-right
        q3 = base.crop((0, mid_y, mid_x, height))      # Bottom-left
        q4 = base.crop((mid_x, mid_y, width, height))  # Bottom-right

        d = random.randint(4, 8)
        # Paste with directional offset
        out.paste(q1, (-d, -d))
        out.paste(q2, (mid_x + d, -d))
        out.paste(q3, (-d, mid_y + d))
        out.paste(q4, (mid_x + d, mid_y + d))

        draw = ImageDraw.Draw(out)
        # Draw intersecting division seams
        draw.line([(mid_x, 0), (mid_x, height)], fill=(235, 69, 158, 160), width=2)
        draw.line([(0, mid_y), (width, mid_y)], fill=(0, 180, 216, 160), width=2)

        self.draw_noise_dots(draw, width, height, count=55)
        return out


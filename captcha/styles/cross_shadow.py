"""
Leakers$ CAPTCHA - CrossShadow Style
Generates multi-directional cross-offset shadows and angled isometric depths.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw, ImageFont
from .base import BaseCaptchaStyle
import config


class CrossShadowStyle(BaseCaptchaStyle):
    """CrossShadow Style: Dual-axis opposing shadow projections."""

    name: str = "CrossShadow"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (245, 245, 248, 255))
        draw = ImageDraw.Draw(img)

        # Angled background lattice lines
        for x in range(-height, width, 18):
            draw.line([(x, 0), (x + height, height)], fill=(230, 230, 238, 255), width=1)
            draw.line([(x + height, 0), (x, height)], fill=(230, 230, 238, 255), width=1)

        num_chars = len(text)
        slot_width = (width - 40) / max(num_chars, 1)
        font = self.get_font(52)

        for i, char in enumerate(text):
            char_canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            c_draw = ImageDraw.Draw(char_canvas)

            # Shadow 1: Bottom-Right (Soft Cyan/Purple)
            c_draw.text((34, 24), char, font=font, fill=(88, 101, 242, 120))
            # Shadow 2: Top-Left (Soft Red/Orange)
            c_draw.text((26, 16), char, font=font, fill=(237, 66, 69, 100))
            # Primary Foreground Character
            c_draw.text((30, 20), char, font=font, fill=(35, 39, 42, 255))

            angle = random.randint(-18, 18)
            rot = char_canvas.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)

            x = int(20 + i * slot_width + random.randint(-3, 3))
            y = int((height - 100) / 2 + random.randint(-5, 5))
            img.paste(rot, (x, y), rot)

        self.draw_noise_dots(draw, width, height, count=50)
        return img


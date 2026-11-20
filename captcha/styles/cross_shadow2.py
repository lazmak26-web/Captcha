"""
Leakers$ CAPTCHA - CrossShadow2 Style
Advanced chromatic cross-shadow projections with dynamic intersecting depth vectors.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw, ImageFont
from .base import BaseCaptchaStyle
import config


class CrossShadow2Style(BaseCaptchaStyle):
    """CrossShadow2 Style: Chromatic 3-layer cross displacement and depth lines."""

    name: str = "CrossShadow2"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (242, 244, 248, 255))
        draw = ImageDraw.Draw(img)

        # Crosshatch vector lines
        for _ in range(16):
            cx, cy = random.randint(0, width), random.randint(0, height)
            length = random.randint(30, 80)
            draw.line([(cx - length, cy - length), (cx + length, cy + length)], fill=(215, 220, 235, 180), width=1)
            draw.line([(cx - length, cy + length), (cx + length, cy - length)], fill=(215, 220, 235, 180), width=1)

        num_chars = len(text)
        slot_width = (width - 40) / max(num_chars, 1)
        font = self.get_font(52)

        for i, char in enumerate(text):
            char_canvas = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
            c_draw = ImageDraw.Draw(char_canvas)

            # Triple chromatic cross shadows
            # Cyan offset (bottom left)
            c_draw.text((27, 27), char, font=font, fill=(0, 200, 220, 130))
            # Magenta offset (top right)
            c_draw.text((37, 17), char, font=font, fill=(235, 69, 158, 130))
            # Yellow offset (bottom right)
            c_draw.text((37, 27), char, font=font, fill=(240, 180, 0, 120))
            # Dark primary text
            c_draw.text((32, 22), char, font=font, fill=(20, 25, 35, 255))

            angle = random.randint(-22, 22)
            rot = char_canvas.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)

            x = int(18 + i * slot_width + random.randint(-4, 4))
            y = int((height - 110) / 2 + random.randint(-6, 6))
            img.paste(rot, (x, y), rot)

        self.draw_noise_dots(draw, width, height, count=80)
        return img


"""
Leakers$ CAPTCHA - Strippy Style
Alternating high-frequency barcode stripes and horizontal zebra scanlines.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class StrippyStyle(BaseCaptchaStyle):
    """Strippy Style: Fine alternating striped scanlines and vertical frequency bars."""

    name: str = "Strippy"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Neutral background
        img = Image.new("RGBA", (width, height), (245, 245, 248, 255))
        draw = ImageDraw.Draw(img)

        # Draw dense background stripes (vertical frequency grating)
        stripe_w = 4
        for x in range(0, width, stripe_w * 2):
            draw.rectangle([(x, 0), (x + stripe_w, height)], fill=(235, 237, 242, 255))

        # Render characters
        chars = self.render_characters_individually(text, width, height, font_size=52, max_angle=16)
        img.paste(chars, (0, 0), chars)

        # Horizontal scanlines overlay
        scanline_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(scanline_layer)

        for y in range(0, height, 4):
            # Alternating semi-transparent horizontal scanline
            s_draw.line([(0, y), (width, y)], fill=(88, 101, 242, 40), width=1)

        # A few bold diagonal highlight stripes
        for _ in range(3):
            sx = random.randint(0, width)
            s_draw.line([(sx, 0), (sx + random.randint(40, 80), height)], fill=(255, 255, 255, 120), width=3)

        img.paste(scanline_layer, (0, 0), scanline_layer)
        self.draw_noise_dots(draw, width, height, count=35)
        return img


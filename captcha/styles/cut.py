"""
Leakers$ CAPTCHA - Cut Style
Slices horizontal/diagonal strata across the characters with offset displacement.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class CutStyle(BaseCaptchaStyle):
    """Cut Style: Sharp razor incisions and sectional coordinate shifting."""

    name: str = "Cut"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Render clean base characters first
        base = self.render_characters_individually(text, width, height, font_size=52, max_angle=12)

        # Create new canvas to receive sliced strips
        cut_img = Image.new("RGBA", (width, height), (245, 245, 245, 255))

        # Perform 3-5 horizontal cuts with alternating left/right displacement
        num_slices = random.randint(4, 6)
        slice_height = height // num_slices

        for s in range(num_slices):
            top = s * slice_height
            bottom = height if s == num_slices - 1 else (s + 1) * slice_height
            crop_box = (0, top, width, bottom)
            strip = base.crop(crop_box)

            # Horizontal displacement shift
            shift_x = random.randint(-9, 9)
            cut_img.paste(strip, (shift_x, top))

        draw = ImageDraw.Draw(cut_img)

        # Draw razor cut incision lines between strips
        for s in range(1, num_slices):
            y_cut = s * slice_height
            draw.line([(0, y_cut), (width, y_cut)], fill=(255, 255, 255, 200), width=1)
            draw.line([(0, y_cut + 1), (width, y_cut + 1)], fill=(120, 120, 130, 80), width=1)

        # Add angled diagonal slash cuts
        for _ in range(2):
            x1 = random.randint(10, width - 50)
            y1 = random.randint(0, 20)
            x2 = x1 + random.randint(20, 60)
            y2 = height - random.randint(0, 20)
            draw.line([(x1, y1), (x2, y2)], fill=(237, 66, 69, 140), width=1)

        self.draw_noise_dots(draw, width, height, count=40)
        return cut_img


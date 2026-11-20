"""
Leakers$ CAPTCHA - Distortion Style
Applies algorithmic sinusoidal wave mesh warp and ripple deformations.
"""

from __future__ import annotations

import math
import random
from PIL import Image, ImageDraw
from .base import BaseCaptchaStyle
import config


class DistortionStyle(BaseCaptchaStyle):
    """Distortion Style: Mathematical wave deformation and ripple distortion."""

    name: str = "Distortion"

    def _apply_sine_wave(self, img: Image.Image, amplitude: float = 6.0, period: float = 40.0) -> Image.Image:
        """Applies horizontal and vertical sine-wave coordinate transformation."""
        width, height = img.size
        warped = Image.new("RGBA", (width, height), (245, 247, 250, 255))
        pixels_in = img.load()
        pixels_out = warped.load()

        phase_x = random.uniform(0, 2 * math.pi)
        phase_y = random.uniform(0, 2 * math.pi)

        for y in range(height):
            for x in range(width):
                # Calculate wave offsets
                offset_x = int(amplitude * math.sin((2 * math.pi * y / period) + phase_x))
                offset_y = int((amplitude / 1.5) * math.cos((2 * math.pi * x / period) + phase_y))

                src_x = x + offset_x
                src_y = y + offset_y

                if 0 <= src_x < width and 0 <= src_y < height:
                    pixels_out[x, y] = pixels_in[src_x, src_y]
                else:
                    pixels_out[x, y] = (245, 247, 250, 255)

        return warped

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Base characters
        base = self.render_characters_individually(text, width, height, font_size=52, max_angle=15)

        # Apply sinusoidal warp
        warped = self._apply_sine_wave(base, amplitude=random.uniform(5.0, 7.5), period=random.uniform(35.0, 50.0))

        draw = ImageDraw.Draw(warped)
        self.draw_noise_lines(draw, width, height, count=3, width_range=(1, 2))
        self.draw_noise_dots(draw, width, height, count=45)

        return warped


"""
Leakers$ CAPTCHA - Corrosion Style
Simulates acidic erosion, rust speckling, and degraded surface textures.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw, ImageFilter
from .base import BaseCaptchaStyle
import config


class CorrosionStyle(BaseCaptchaStyle):
    """Corrosion Style: Weathered rust streaks, acid pits, and edge erosion."""

    name: str = "Corrosion"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Grimy metallic backdrop
        img = Image.new("RGBA", (width, height), (225, 222, 215, 255))
        draw = ImageDraw.Draw(img)

        # Base characters
        base = self.render_characters_individually(text, width, height, font_size=52, max_angle=18)
        img.paste(base, (0, 0), base)

        # Create corrosion speckle layer
        corrosion_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(corrosion_layer)

        # Acid bite pits (circular holes and dark blotches)
        for _ in range(350):
            px = random.randint(0, width)
            py = random.randint(0, height)
            pr = random.randint(1, 4)
            # Rust / corrosion hues: reddish browns and toxic ochre
            rust_colors = [
                (140, 50, 20, random.randint(140, 220)),
                (180, 85, 35, random.randint(130, 210)),
                (70, 75, 60, random.randint(100, 180)),
                (230, 225, 210, random.randint(180, 255)),  # bleached spots
            ]
            c_draw.ellipse([(px - pr, py - pr), (px + pr, py + pr)], fill=random.choice(rust_colors))

        # Rust streaks dripping down
        for _ in range(14):
            sx = random.randint(0, width)
            sy = random.randint(0, height // 2)
            length = random.randint(15, 45)
            c_draw.line([(sx, sy), (sx + random.randint(-4, 4), sy + length)], fill=(130, 55, 25, 160), width=random.randint(1, 2))

        img.paste(corrosion_layer, (0, 0), corrosion_layer)

        # Apply slight edge sharpen to accentuate erosion
        return img.filter(ImageFilter.EDGE_ENHANCE_MORE)


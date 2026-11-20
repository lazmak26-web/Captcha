"""
Leakers$ CAPTCHA - Collage Style
Simulates multi-layered paper/card cutouts with textured geometric backdrops.
"""

from __future__ import annotations

import random
from PIL import Image, ImageDraw, ImageFont
from .base import BaseCaptchaStyle
import config


class CollageStyle(BaseCaptchaStyle):
    """Collage Style: Renders letters onto layered, rotated paper cards."""

    name: str = "Collage"

    def generate(
        self,
        text: str,
        width: int = config.CAPTCHA_IMAGE_WIDTH,
        height: int = config.CAPTCHA_IMAGE_HEIGHT,
    ) -> Image.Image:
        # Base background canvas with neutral pastel fill
        img = Image.new("RGBA", (width, height), (235, 238, 245, 255))
        draw = ImageDraw.Draw(img)

        # Draw decorative background collage polygons
        for _ in range(8):
            pts = [
                (random.randint(0, width), random.randint(0, height)),
                (random.randint(0, width), random.randint(0, height)),
                (random.randint(0, width), random.randint(0, height)),
            ]
            fill_color = self.random_accent_color(alpha=random.randint(40, 90))
            draw.polygon(pts, fill=fill_color)

        num_chars = len(text)
        slot_width = (width - 40) / max(num_chars, 1)
        font = self.get_font(48)

        # Render each character on an independent rotated card
        for i, char in enumerate(text):
            card_w, card_h = 56, 74
            card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card)

            # Paper card base with subtle outline
            card_bg = (random.randint(240, 255), random.randint(240, 255), random.randint(240, 255), 245)
            card_draw.rounded_rectangle([(2, 2), (card_w - 3, card_h - 3)], radius=6, fill=card_bg, outline=(180, 180, 195, 200), width=2)

            # Draw character centered on card
            text_color = self.random_dark_color()
            card_draw.text((14, 8), char, font=font, fill=text_color)

            # Rotate paper card
            card_rot = card.rotate(random.randint(-18, 18), resample=Image.Resampling.BICUBIC, expand=True)

            x = int(18 + i * slot_width + random.randint(-4, 4))
            y = int((height - card_h) / 2 + random.randint(-8, 8))
            img.paste(card_rot, (x, y), card_rot)

        # Overlay scattered micro-noise
        self.draw_noise_dots(draw, width, height, count=70)
        self.draw_noise_lines(draw, width, height, count=3, width_range=(1, 2))

        return img


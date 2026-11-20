"""
Leakers$ CAPTCHA - Base Style & Graphical Utilities
Defines abstract style contract, font resolvers, and geometric transformation utilities.
"""

from __future__ import annotations

import io
import math
import os
import random
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config


class BaseCaptchaStyle(ABC):
    """Abstract Base Class for all visual CAPTCHA styles."""

    name: str = "Base"

    def __init__(self) -> None:
        self.font_paths = self._discover_system_fonts()

    @staticmethod
    def _discover_system_fonts() -> list[str]:
        """Discovers usable scalable TrueType fonts across Windows and Linux."""
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ]
        return [p for p in candidates if os.path.exists(p)]

    def get_font(self, size: int = 50) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Returns a FreeType font or falls back to PIL default font."""
        for path in self.font_paths:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    @staticmethod
    def random_dark_color(alpha: int = 255) -> Tuple[int, int, int, int]:
        """Generates a random dark color for legible text contrast."""
        r = random.randint(20, 110)
        g = random.randint(20, 110)
        b = random.randint(20, 110)
        return (r, g, b, alpha)

    @staticmethod
    def random_light_color(alpha: int = 255) -> Tuple[int, int, int, int]:
        """Generates a random light color for backgrounds and highlights."""
        r = random.randint(220, 255)
        g = random.randint(220, 255)
        b = random.randint(220, 255)
        return (r, g, b, alpha)

    @staticmethod
    def random_accent_color(alpha: int = 255) -> Tuple[int, int, int, int]:
        """Generates a random vibrant accent color for lines/shapes."""
        colors = [
            (88, 101, 242, alpha),   # Blurple
            (235, 69, 158, alpha),   # Fuchsia
            (87, 242, 135, alpha),   # Green
            (254, 231, 92, alpha),   # Yellow
            (237, 66, 69, alpha),    # Red
            (0, 180, 216, alpha),    # Cyan
        ]
        return random.choice(colors)

    def draw_noise_dots(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        count: int = 150,
    ) -> None:
        """Adds scattered noise dots to deter simple OCR."""
        for _ in range(count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(1, 3)
            color = self.random_accent_color(alpha=random.randint(120, 220))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    def draw_noise_lines(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        count: int = 5,
        width_range: Tuple[int, int] = (1, 3),
    ) -> None:
        """Draws intersecting curved or straight distraction lines."""
        for _ in range(count):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            lw = random.randint(*width_range)
            draw.line([(x1, y1), (x2, y2)], fill=self.random_accent_color(alpha=180), width=lw)

    def render_characters_individually(
        self,
        text: str,
        width: int,
        height: int,
        font_size: int = 52,
        max_angle: int = 25,
    ) -> Image.Image:
        """
        Renders each character with random rotation, slight scaling, and positioning
        onto a transparent RGBA canvas, then pastes onto a soft gradient background.
        """
        bg = Image.new("RGBA", (width, height), (245, 247, 250, 255))
        # Add subtle vertical gradient
        bg_draw = ImageDraw.Draw(bg)
        for y in range(height):
            shade = int(245 - (y / height) * 20)
            bg_draw.line([(0, y), (width, y)], fill=(shade, shade, shade + 5, 255))

        char_canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        font = self.get_font(font_size)

        num_chars = len(text)
        slot_width = (width - 40) / max(num_chars, 1)

        for i, char in enumerate(text):
            # Render character into temporary surface
            char_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            color = self.random_dark_color()

            # Center text in temp surface
            char_draw.text((30, 20), char, font=font, fill=color)

            # Apply random rotation
            angle = random.randint(-max_angle, max_angle)
            rotated_char = char_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)

            # Position onto main canvas
            x_pos = int(20 + i * slot_width + random.randint(-4, 4))
            y_pos = int((height - 100) / 2 + random.randint(-6, 6))
            char_canvas.paste(rotated_char, (x_pos, y_pos), rotated_char)

        bg.paste(char_canvas, (0, 0), char_canvas)
        return bg

    @abstractmethod
    def generate(self, text: str, width: int = config.CAPTCHA_IMAGE_WIDTH, height: int = config.CAPTCHA_IMAGE_HEIGHT) -> Image.Image:
        """Core rendering contract to be implemented by each specific style."""
        raise NotImplementedError

    def to_bytes(self, image: Image.Image) -> bytes:
        """Encodes PIL Image into optimized PNG byte stream."""
        buffer = io.BytesIO()
        rgb_image = image.convert("RGB")
        rgb_image.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        return buffer.getvalue()


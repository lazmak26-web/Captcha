"""
Leakers$ CAPTCHA - Darknet Market Shapes Instruction Style
Faithful implementation of the security forum / market geometric instruction CAPTCHA.
Instructs user to read only digits inside specific shapes (Circles, Triangles, Squares, Diamonds).
Rendered at crisp high-resolution (1024x672) for razor-sharp display in Discord.
"""

from __future__ import annotations

import io
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont

from .base import BaseCaptchaStyle
import config


@dataclass
class ShapeItem:
    shape_type: str  # 'circle', 'triangle', 'square', 'diamond'
    digit: str
    grid_index: int  # 0 to 9 (row 0: 0-4, row 1: 5-9)
    cx: int
    cy: int
    color: Tuple[int, int, int]
    is_double: bool
    digit_angle: int = 0


class MarketShapesStyle(BaseCaptchaStyle):
    """
    Market / Darknet Security Check Style.
    Renders 10 geometric shapes across two rows with scattered background watermarks.
    The secret answer is the digits inside the instructed target shapes in reading order.
    """

    name: str = "MarketShapes"

    SHAPES = ["circle", "triangle", "square", "diamond"]
    SHAPE_PLURALS = {
        "circle": "CIRCLES",
        "triangle": "TRIANGLES",
        "square": "SQUARES",
        "diamond": "DIAMONDS",
    }

    # Monochrome dark theme palette matching the authentic market security check
    SHAPE_COLORS = [
        (250, 250, 250),  # Crisp White
    ]

    WATERMARK_WORDS = [
        "https://leakers.site/",
    ]

    def _get_mono_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Returns monospaced or clean sans font for headers/footers."""
        mono_candidates = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
            "C:/Windows/Fonts/lucon.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
        for p in mono_candidates:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return self.get_font(size)

    def _get_bold_font(self, size: int = 48) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Returns heavy bold font for the prominent translucent watermarks."""
        bold_candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/tahomabd.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for p in bold_candidates:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return self.get_font(size)

    def _get_digit_font(self, size: int = 38) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Returns bold monospaced font matching the authentic market check digits."""
        candidates = [
            "C:/Windows/Fonts/consolab.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/courbd.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        ]
        for p in candidates:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return self.get_font(size)

    def _draw_shape(
        self,
        draw: ImageDraw.ImageDraw,
        shape: ShapeItem,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        scale: float = 1.0,
    ) -> None:
        cx, cy = shape.cx, shape.cy
        color = shape.color
        is_double = shape.is_double

        if shape.shape_type == "circle":
            r = int(30 * scale)
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=color, width=max(2, int(2.5 * scale)))
            if is_double:
                diff = int(5 * scale)
                draw.ellipse([(cx - r + diff, cy - r + diff), (cx + r - diff, cy + r - diff)], outline=color, width=max(1, int(1.5 * scale)))

        elif shape.shape_type == "square":
            s = int(26 * scale)
            draw.rectangle([(cx - s, cy - s), (cx + s, cy + s)], outline=color, width=max(2, int(3.0 * scale)))
            if is_double:
                diff = int(4 * scale)
                draw.rectangle([(cx - s + diff, cy - s + diff), (cx + s - diff, cy + s - diff)], outline=color, width=max(1, int(1.5 * scale)))

        elif shape.shape_type == "triangle":
            # Upright triangle
            h = int(32 * scale)
            w = int(30 * scale)
            b_offset = int(6 * scale)
            pts = [(cx, cy - h), (cx - w, cy + h - b_offset), (cx + w, cy + h - b_offset)]
            draw.polygon(pts, outline=color, width=max(2, int(3.0 * scale)))
            if is_double:
                # Double line near base
                line_y = cy + h - int(2 * scale)
                draw.line([(cx - w + int(4 * scale), line_y), (cx + w - int(4 * scale), line_y)], fill=color, width=max(1, int(2.0 * scale)))

        elif shape.shape_type == "diamond":
            d = int(32 * scale)
            pts = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
            draw.polygon(pts, outline=color, width=max(2, int(3.0 * scale)))
            if is_double:
                d_in = d - int(5 * scale)
                pts_in = [(cx, cy - d_in), (cx + d_in, cy), (cx, cy + d_in), (cx - d_in, cy)]
                draw.polygon(pts_in, outline=color, width=max(1, int(1.5 * scale)))

        # Draw the digit centered inside the shape
        bbox = font.getbbox(shape.digit)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = cx - text_w // 2 - bbox[0]
        text_y = cy - text_h // 2 - bbox[1]
        if shape.shape_type == "triangle":
            text_y += int(4 * scale)

        draw.text((text_x, text_y), shape.digit, font=font, fill=color)

    def generate_challenge(
        self,
        width: int = 1024,
        height: int = 672,
    ) -> Tuple[Image.Image, str]:
        """
        Generates the market instruction CAPTCHA image and returns (Image, correct_code).
        The challenge picks a random target shape, populates 10 shapes in a 2x5 grid,
        and computes the code from target shapes ordered row-by-row, left-to-right.
        Default resolution is 1024x672 for ultra-crisp display in Discord.
        """
        scale = width / 640.0
        img = Image.new("RGB", (width, height), (26, 26, 26))
        draw = ImageDraw.Draw(img)

        # Scaled Fonts
        header_font_sm = self._get_mono_font(int(13 * scale))
        header_font_bold = self._get_mono_font(int(16 * scale))
        digit_font = self._get_digit_font(int(38 * scale))
        footer_bold = self._get_mono_font(int(13 * scale))
        faint_font = self._get_mono_font(int(13 * scale))

        # 1. Target shape selection
        target_shape = random.choice(self.SHAPES)
        target_plural = self.SHAPE_PLURALS[target_shape]

        # Exactly 5 target shapes (matching user instruction to enter five requested digits)
        target_count = 5
        other_shapes = [s for s in self.SHAPES if s != target_shape]

        # 10 grid slots: row 0 (0..4), row 1 (5..9)
        all_indices = list(range(10))
        target_indices = set(random.sample(all_indices, target_count))

        # 2. Header instructions (Dark Monochrome)
        draw.text(
            (int(15 * scale), int(14 * scale)),
            "SECURITY CHECK - FOLLOW THE IMAGE INSTRUCTION",
            font=header_font_sm,
            fill=(168, 168, 168),
        )
        draw.text(
            (int(15 * scale), int(36 * scale)),
            f"READ ONLY THE DIGITS INSIDE {target_plural}",
            font=header_font_bold,
            fill=(165, 165, 165),
        )

        # 3. Main challenge box
        box_left = int(12 * scale)
        box_top = int(64 * scale)
        box_right = width - int(12 * scale)
        box_bottom = height - int(60 * scale)
        draw.rectangle(
            [(box_left, box_top), (box_right, box_bottom)],
            outline=(60, 60, 60),
            width=max(1, int(1.2 * scale)),
        )

        # 4. Background security watermarks & hairlines inside the box
        watermark_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(watermark_layer)

        # 4A. Prominent bold "https://leakers.site/" watermarks (Dark Theme)
        big_wm_font = self._get_bold_font(int(44 * scale))
        med_wm_font = self._get_bold_font(int(30 * scale))

        # Main prominent center watermark: "https://leakers.site/"
        c_w, c_h = int(550 * scale), int(80 * scale)
        center_wm = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(center_wm)
        c_draw.text((int(10 * scale), int(8 * scale)), "https://leakers.site/", font=big_wm_font, fill=(185, 185, 185, 115))
        rot_center = center_wm.rotate(-14, resample=Image.Resampling.BICUBIC, expand=True)
        watermark_layer.paste(rot_center, (width // 2 - int(200 * scale), box_top + int(45 * scale)), rot_center)

        # Prominent watermark 2: top-left area "https://leakers.site/"
        tl_w, tl_h = int(420 * scale), int(60 * scale)
        tl_wm = Image.new("RGBA", (tl_w, tl_h), (0, 0, 0, 0))
        tl_draw = ImageDraw.Draw(tl_wm)
        tl_draw.text((int(10 * scale), int(8 * scale)), "https://leakers.site/", font=med_wm_font, fill=(160, 160, 160, 95))
        rot_tl = tl_wm.rotate(12, resample=Image.Resampling.BICUBIC, expand=True)
        watermark_layer.paste(rot_tl, (box_left + int(15 * scale), box_top + int(10 * scale)), rot_tl)

        # Prominent watermark 3: bottom-right area "https://leakers.site/"
        br_w, br_h = int(420 * scale), int(60 * scale)
        br_wm = Image.new("RGBA", (br_w, br_h), (0, 0, 0, 0))
        br_draw = ImageDraw.Draw(br_wm)
        br_draw.text((int(10 * scale), int(6 * scale)), "https://leakers.site/", font=med_wm_font, fill=(160, 160, 160, 95))
        rot_br = br_wm.rotate(-10, resample=Image.Resampling.BICUBIC, expand=True)
        watermark_layer.paste(rot_br, (width - int(320 * scale), box_bottom - int(75 * scale)), rot_br)

        # 4B. Background URL strings (only https://leakers.site/)
        for _ in range(8):
            wm_text = "https://leakers.site/"
            angle = random.randint(-20, 20)
            wx = random.randint(box_left + int(10 * scale), box_right - int(220 * scale))
            wy = random.randint(box_top + int(10 * scale), box_bottom - int(30 * scale))

            txt_img = Image.new("RGBA", (int(320 * scale), int(40 * scale)), (0, 0, 0, 0))
            t_draw = ImageDraw.Draw(txt_img)
            t_draw.text((int(5 * scale), int(5 * scale)), wm_text, font=faint_font, fill=(130, 130, 130, 80))
            rot_txt = txt_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
            watermark_layer.paste(rot_txt, (wx, wy), rot_txt)

        # Thin hairline scratch lines
        for _ in range(16):
            lx1 = random.randint(box_left, box_right)
            ly1 = random.randint(box_top, box_bottom)
            lx2 = lx1 + random.randint(int(-90 * scale), int(90 * scale))
            ly2 = ly1 + random.randint(int(-40 * scale), int(40 * scale))
            wm_draw.line([(lx1, ly1), (lx2, ly2)], fill=(75, 75, 75, 130), width=max(1, int(1.2 * scale)))

        # Scattered noise dots
        for _ in range(60):
            nx = random.randint(box_left, box_right)
            ny = random.randint(box_top, box_bottom)
            dot_size = max(1, int(1.5 * scale))
            wm_draw.rectangle([(nx, ny), (nx + dot_size, ny + dot_size)], fill=(85, 85, 85, 150))

        img.paste(watermark_layer, (0, 0), watermark_layer)
        draw = ImageDraw.Draw(img)

        # 5. Populate and render the 10 shapes (2 rows x 5 columns)
        shapes_list: List[ShapeItem] = []
        col_width = (box_right - box_left) // 5
        row_height = (box_bottom - box_top) // 2

        digits = [str(random.randint(2, 9)) for _ in range(10)]

        for idx in range(10):
            row = idx // 5
            col = idx % 5

            cx = box_left + int((col + 0.5) * col_width) + random.randint(int(-3 * scale), int(3 * scale))
            cy = box_top + int((row + 0.5) * row_height) + random.randint(int(-3 * scale), int(3 * scale))

            stype = target_shape if idx in target_indices else random.choice(other_shapes)
            color = random.choice(self.SHAPE_COLORS)
            is_dbl = random.random() < 0.65

            item = ShapeItem(
                shape_type=stype,
                digit=digits[idx],
                grid_index=idx,
                cx=cx,
                cy=cy,
                color=color,
                is_double=is_dbl,
            )
            shapes_list.append(item)
            self._draw_shape(draw, item, digit_font, scale=scale)

        # Multi-layer foreground security scratches (anti-segmentation / anti-thresholding)
        fg_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        fg_draw = ImageDraw.Draw(fg_layer)
        for _ in range(8):
            lx1 = random.randint(box_left, box_right)
            ly1 = random.randint(box_top, box_bottom)
            lx2 = lx1 + random.randint(int(-110 * scale), int(110 * scale))
            ly2 = ly1 + random.randint(int(-45 * scale), int(45 * scale))
            fg_draw.line([(lx1, ly1), (lx2, ly2)], fill=(70, 70, 70, 110), width=max(1, int(1.2 * scale)))
        img.paste(fg_layer, (0, 0), fg_layer)

        # 6. Compute target answer in reading order (row 0 then row 1, left to right)
        target_digits = [item.digit for item in shapes_list if item.grid_index in target_indices]
        correct_code = "".join(target_digits)

        # 7. Bottom footer notice (Dark Monochrome)
        draw.text(
            (int(15 * scale), height - int(44 * scale)),
            "OFFICIAL ADDRESS - VERIFY YOUR BOOKMARK / URL CAREFULLY:",
            font=footer_bold,
            fill=(152, 152, 152),
        )
        draw.text(
            (int(15 * scale), height - int(25 * scale)),
            "https://leakers.site/",
            font=footer_bold,
            fill=(255, 255, 255),
        )

        return img, correct_code

    def generate(
        self,
        text: str,
        width: int = 1024,
        height: int = 672,
    ) -> Image.Image:
        """Standard interface compatibility with BaseCaptchaStyle."""
        img, _ = self.generate_challenge(width=width, height=height)
        return img

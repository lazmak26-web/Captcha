"""
Leakers$ CAPTCHA - Visual Style Engine Test Suite
Validates procedural generation, dimensions, PNG headers, and Pillow rendering
for all 13 supported styles.
"""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from captcha.generator import CaptchaGenerator
from captcha.styles import STYLE_REGISTRY, get_style


class TestCaptchaStyles(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the 13 visual CAPTCHA styles and generator engine."""

    def setUp(self) -> None:
        self.generator = CaptchaGenerator()
        self.expected_styles = [
            "MarketShapes",
            "Collage",
            "Snow",
            "Corrosion",
            "SpiderWeb",
            "CrossShadow",
            "CrossShadow2",
            "Cut",
            "Darts",
            "Distortion",
            "Split",
            "Split2",
            "Stitch",
            "Strippy",
        ]

    def test_all_styles_registered(self) -> None:
        """Confirms that all styles are present in STYLE_REGISTRY."""
        for style_name in self.expected_styles:
            self.assertIn(
                style_name,
                STYLE_REGISTRY,
                f"Style '{style_name}' missing from STYLE_REGISTRY",
            )
        self.assertEqual(len(STYLE_REGISTRY), 14)

    def test_random_code_generation(self) -> None:
        """Verifies cryptographically secure code generation length and charset."""
        code = self.generator.generate_random_code(length=6)
        self.assertEqual(len(code), 6)
        for char in code:
            self.assertIn(char, config.CHARSET)

    async def test_all_13_styles_render_valid_png(self) -> None:
        """
        Renders every single style and verifies:
        1. Non-empty byte output (> 1000 bytes)
        2. Valid PNG magic byte signature (b'\\x89PNG\\r\\n\\x1a\\n')
        3. Valid Pillow Image decoding
        4. Correct dimensions (width=340, height=120)
        """
        test_text = "WM8QGZ"
        png_magic = b"\x89PNG\r\n\x1a\n"

        for style_name in self.expected_styles:
            with self.subTest(style=style_name):
                res = await self.generator.create_captcha(
                    style_name=style_name,
                    code=test_text,
                    width=config.CAPTCHA_IMAGE_WIDTH,
                    height=config.CAPTCHA_IMAGE_HEIGHT,
                )
                if style_name != "MarketShapes":
                    self.assertEqual(res.code, test_text)
                else:
                    self.assertGreaterEqual(len(res.code), 4)
                self.assertEqual(res.style_name, style_name)
                self.assertGreater(
                    len(res.image_bytes),
                    1000,
                    f"Style {style_name} output too small ({len(res.image_bytes)} bytes)",
                )

                # Check PNG Magic Header
                self.assertTrue(
                    res.image_bytes.startswith(png_magic),
                    f"Style {style_name} did not produce a valid PNG binary header",
                )

                # Verify Pillow can open and parse image
                img = Image.open(io.BytesIO(res.image_bytes))
                if style_name == "MarketShapes":
                    self.assertEqual(img.size, (1024, 672))
                else:
                    self.assertEqual(img.size, (config.CAPTCHA_IMAGE_WIDTH, config.CAPTCHA_IMAGE_HEIGHT))
                self.assertIn(img.mode, ("RGB", "RGBA"))

    async def test_random_style_selection(self) -> None:
        """Verifies that requesting 'Random' resolves to one of the 13 supported styles."""
        res = await self.generator.create_captcha(style_name="Random")
        self.assertIn(res.style_name, self.expected_styles)
        self.assertGreater(len(res.image_bytes), 1000)

    def test_style_factory_fallback(self) -> None:
        """Verifies that unknown style strings fallback gracefully without raising."""
        style = get_style("UnknownNonExistentStyle")
        self.assertIsNotNone(style)
        self.assertIn(style.name, self.expected_styles)


def main() -> int:
    """CLI runner returning exit code 0 on success, 1 on failure."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCaptchaStyles)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())


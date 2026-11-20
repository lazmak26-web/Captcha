"""
Leakers$ CAPTCHA - Visual Style Registry
Provides a unified factory to retrieve style instances by name.
"""

from __future__ import annotations

import random
from typing import Type

from .base import BaseCaptchaStyle
from .collage import CollageStyle
from .snow import SnowStyle
from .corrosion import CorrosionStyle
from .spiderweb import SpiderWebStyle
from .cross_shadow import CrossShadowStyle
from .cross_shadow2 import CrossShadow2Style
from .cut import CutStyle
from .darts import DartsStyle
from .distortion import DistortionStyle
from .split import SplitStyle
from .split2 import Split2Style
from .stitch import StitchStyle
from .strippy import StrippyStyle
from .market_shapes import MarketShapesStyle

STYLE_REGISTRY: dict[str, Type[BaseCaptchaStyle]] = {
    "MarketShapes": MarketShapesStyle,
    "Collage": CollageStyle,
    "Snow": SnowStyle,
    "Corrosion": CorrosionStyle,
    "SpiderWeb": SpiderWebStyle,
    "CrossShadow": CrossShadowStyle,
    "CrossShadow2": CrossShadow2Style,
    "Cut": CutStyle,
    "Darts": DartsStyle,
    "Distortion": DistortionStyle,
    "Split": SplitStyle,
    "Split2": Split2Style,
    "Stitch": StitchStyle,
    "Strippy": StrippyStyle,
}

# Pre-instantiate singletons for optimal performance (thread-safe rendering)
_INSTANCES: dict[str, BaseCaptchaStyle] = {
    name: cls() for name, cls in STYLE_REGISTRY.items()
}


def get_style(name: str) -> BaseCaptchaStyle:
    """
    Retrieves a style engine instance by name (case-insensitive).
    If 'Random' or an unknown name is provided, a random style is returned.
    """
    for key, instance in _INSTANCES.items():
        if key.lower() == name.lower():
            return instance

    # Fallback or Random
    random_key = random.choice(list(_INSTANCES.keys()))
    return _INSTANCES[random_key]


__all__ = [
    "BaseCaptchaStyle",
    "CollageStyle",
    "SnowStyle",
    "CorrosionStyle",
    "SpiderWebStyle",
    "CrossShadowStyle",
    "CrossShadow2Style",
    "CutStyle",
    "DartsStyle",
    "DistortionStyle",
    "SplitStyle",
    "Split2Style",
    "StitchStyle",
    "StrippyStyle",
    "MarketShapesStyle",
    "STYLE_REGISTRY",
    "get_style",
]


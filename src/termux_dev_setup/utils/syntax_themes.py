# syntax_themes.py

"""Standalone theme utility for Pygments-based syntax styling.

Provides:
 - Several static Style subclasses (dracula, one_dark, tokyo_night, ...)
 - A random theme generator with deterministic-seed option
 - A single public helper `get_syntax_theme(name: str)` that returns (StyleClass, background_hex)

Usage:
    from syntax_themes import get_syntax_theme
    StyleClass, bg = get_syntax_theme("dracula")
    StyleClass, bg = get_syntax_theme("random")         # ephemeral random
    StyleClass, bg = get_syntax_theme("random:12345")   # deterministic by seed
"""

from __future__ import annotations
import random
from typing import Tuple, Dict
from pygments.style import Style
from pygments.token import (
    Token,
    Comment,
    Keyword,
    Name,
    Literal,
    String,
    Number,
    Operator,
    Generic,
    Text,
)


# ----------------------------
# 1. CyberpunkStyle
# Best match for established aesthetic preferences.
# ----------------------------
class CyberpunkStyle(Style):
    background_color = "#0b0f19"
    default_style = "#f8f8f2"
    styles = {
        Comment: "italic #6b6b6b",
        Keyword: "bold #ff3d81",
        Keyword.Declaration: "bold #ff3d81",
        Name: "#f8f8f2",
        Name.Function: "#7ef1ff",
        Name.Builtin: "#ffd55a",
        Name.Decorator: "#ff3d81",
        Name.Class: "#ffd55a",
        String: "#7ef17e",
        Number: "#ff7ac6",
        Operator: "#f8f8f2",
        Literal: "#ffb86c",
        Generic: "#9aa7c7",
        Token.LineNumber: "#444444",
        Token.LineNumber.Current: "bold #ff3d81",
        Text: "#f8f8f2",
    }

# ----------------------------
# 2. EyeCandyStyle
# High saturation neon colors that pop in a terminal.
# ----------------------------
class EyeCandyStyle(Style):
    background_color = "#0f1020"
    default_style = "#f5f7ff"
    styles = {
        Comment: "italic #9aa0a6",
        Keyword: "bold #7ee787",
        Keyword.Declaration: "bold #7ee787",
        Name: "#f5f7ff",
        Name.Function: "#ff9ed8",
        Name.Builtin: "#ffd08a",
        Name.Decorator: "#7ee787",
        Name.Class: "#ffd08a",
        String: "#7ef1c7",
        Number: "#b39cff",
        Operator: "#f5f7ff",
        Literal: "#ffcf7e",
        Generic: "#9fb1c1",
        Token.LineNumber: "#2b2b44",
        Token.LineNumber.Current: "bold #7ee787",
        Text: "#f5f7ff",
    }

# ----------------------------
# 3. TokyoNightStyle
# Modern, professional deep-dark theme.
# ----------------------------
class TokyoNightStyle(Style):
    background_color = "#1a1b27"
    default_style = "#c0caf5"
    styles = {
        Comment: "italic #565f89",
        Keyword: "bold #ff9e64",
        Keyword.Declaration: "bold #ff9e64",
        Name: "#c0caf5",
        Name.Function: "#7aa2f7",
        Name.Builtin: "#7dcfff",
        Name.Decorator: "#ff9e64",
        Name.Class: "#7dcfff",
        String: "#9ece6a",
        Number: "#d6786e",
        Operator: "#c0caf5",
        Literal: "#e0af68",
        Generic: "#98c379",
        Token.LineNumber: "#2c2f44",
        Token.LineNumber.Current: "bold #7aa2f7",
        Text: "#c0caf5",
    }

# ----------------------------
# 4. DraculaLikeStyle
# High contrast and classic dark theme reliability.
# ----------------------------
class DraculaLikeStyle(Style):
    background_color = "#282a36"
    default_style = "#f8f8f2"
    styles = {
        Comment: "italic #6272a4",
        Keyword: "bold #ff79c6",
        Keyword.Declaration: "bold #ff79c6",
        Name: "#f8f8f2",
        Name.Function: "#50fa7b",
        Name.Builtin: "#8be9fd",
        Name.Decorator: "#ff79c6",
        Name.Class: "#8be9fd",
        String: "#f1fa8c",
        Number: "#bd93f9",
        Operator: "#f8f8f2",
        Literal: "#ffb86c",
        Generic: "#9aa7c7",
        Token.LineNumber: "#5c6370",
        Token.LineNumber.Current: "bold #ff79c6",
        Text: "#f8f8f2",
    }

# ----------------------------
# 5. OneDarkStyle
# Balanced atom-like dark theme.
# ----------------------------
class OneDarkStyle(Style):
    background_color = "#282c34"
    default_style = "#abb2bf"
    styles = {
        Comment: "italic #5c6370",
        Keyword: "bold #c678dd",
        Keyword.Declaration: "bold #c678dd",
        Name: "#abb2bf",
        Name.Function: "#61afef",
        Name.Builtin: "#e5c07b",
        Name.Decorator: "#c678dd",
        Name.Class: "#e5c07b",
        String: "#98c379",
        Number: "#56b6c2",
        Operator: "#abb2bf",
        Literal: "#d19a66",
        Generic: "#9aa7b0",
        Token.LineNumber: "#4b5263",
        Token.LineNumber.Current: "bold #c678dd",
        Text: "#abb2bf",
    }

# ----------------------------
# 6. NordStyle
# Arctic, north-bluish clean theme.
# ----------------------------
class NordStyle(Style):
    background_color = "#2e3440"
    default_style = "#d8dee9"
    styles = {
        Comment: "italic #616e88",
        Keyword: "bold #81a1c1",
        Keyword.Declaration: "bold #81a1c1",
        Name: "#d8dee9",
        Name.Function: "#88c0d0",
        Name.Builtin: "#8fbcbb",
        Name.Decorator: "#81a1c1",
        Name.Class: "#8fbcbb",
        String: "#a3be8c",
        Number: "#b48ead",
        Operator: "#d8dee9",
        Literal: "#ebcb8b",
        Generic: "#94a3b8",
        Token.LineNumber: "#3b4252",
        Token.LineNumber.Current: "bold #81a1c1",
        Text: "#d8dee9",
    }


# ----------------------------
# THEME MAP (name -> (StyleClass, bg_hex))
# ----------------------------
THEME_MAP: Dict[str, Tuple[type, str]] = {
    "cyberpunk": (CyberpunkStyle, CyberpunkStyle.background_color),
    "eyecandy": (EyeCandyStyle, EyeCandyStyle.background_color),
    "tokyo_night": (TokyoNightStyle, TokyoNightStyle.background_color),
    "one_dark": (OneDarkStyle, OneDarkStyle.background_color),
    "dracula": (DraculaLikeStyle, DraculaLikeStyle.background_color),
    "nord": (NordStyle, NordStyle.background_color),
}

# ---------- Random theme generator (kept from original) ----------
_MIN_CONTRAST = 4.5
_RANDOM_THEME_CACHE: Dict[str, Tuple[type, str]] = {}

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def hsl_to_rgb(h: float, s: float, lightness: float) -> Tuple[int, int, int]:
    c = (1 - abs(2 * lightness - 1)) * s
    hp = h / 60.0
    x = c * (1 - abs((hp % 2) - 1))
    if 0 <= hp < 1:
        r1, g1, b1 = c, x, 0
    elif 1 <= hp < 2:
        r1, g1, b1 = x, c, 0
    elif 2 <= hp < 3:
        r1, g1, b1 = 0, c, x
    elif 3 <= hp < 4:
        r1, g1, b1 = 0, x, c
    elif 4 <= hp < 5:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    m = lightness - c/2
    r, g, b = r1 + m, g1 + m, b1 + m
    return (int(round(255*clamp01(r))),
            int(round(255*clamp01(g))),
            int(round(255*clamp01(b))))

def rgb_to_hex(rgb: Tuple[int,int,int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    return rgb_to_hex(hsl_to_rgb(h % 360, clamp01(s), clamp01(lightness)))

def relative_luminance(hex_color: str) -> float:
    r = int(hex_color[1:3], 16) / 255.0
    g = int(hex_color[3:5], 16) / 255.0
    b = int(hex_color[5:7], 16) / 255.0
    def lin(c):
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

def contrast_ratio(hex1: str, hex2: str) -> float:
    L1 = relative_luminance(hex1)
    L2 = relative_luminance(hex2)
    lighter, darker = max(L1, L2), min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)

def _choose_harmony_hues(rand: random.Random, base_h: float) -> Tuple[float, float, float]:
    mode = rand.choice(["analogous", "triadic", "complementary", "split"])
    if mode == "analogous":
        return (base_h,
                (base_h + rand.uniform(15, 45)) % 360,
                (base_h - rand.uniform(15, 45)) % 360)
    if mode == "triadic":
        return (base_h, (base_h + 120) % 360, (base_h + 240) % 360)
    if mode == "complementary":
        return (base_h, (base_h + 180) % 360, (base_h + rand.uniform(10, 40)) % 360)
    return (base_h, (base_h + 150) % 360, (base_h - 150) % 360)

def _ensure_contrast(fg_hex: str, bg_hex: str, min_ratio: float = _MIN_CONTRAST) -> str:
    if contrast_ratio(fg_hex, bg_hex) >= min_ratio:
        return fg_hex
    def mix(hexc, with_white: bool, amount: float) -> str:
        r1 = int(hexc[1:3], 16)
        g1 = int(hexc[3:5], 16)
        b1 = int(hexc[5:7], 16)
        if with_white:
            r2, g2, b2 = 255, 255, 255
        else:
            r2, g2, b2 = 0, 0, 0
        r = int(round(r1*(1-amount) + r2*amount))
        g = int(round(g1*(1-amount) + g2*amount))
        b = int(round(b1*(1-amount) + b2*amount))
        return "#{:02x}{:02x}{:02x}".format(r, g, b)
    for amt in [i/20.0 for i in range(1, 20)]:
        c1 = mix(fg_hex, True, amt)
        if contrast_ratio(c1, bg_hex) >= min_ratio:
            return c1
        c2 = mix(fg_hex, False, amt)
        if contrast_ratio(c2, bg_hex) >= min_ratio:
            return c2
    return fg_hex

def generate_random_theme(seed: int = None, prefer_dark: bool = True) -> Tuple[type, str]:
    rand = random.Random(seed)
    is_dark = rand.random() < (0.85 if prefer_dark else 0.15)
    bg_hue = rand.uniform(0, 360)
    if is_dark:
        bg_light = rand.uniform(0.06, 0.18)
        text_light = rand.uniform(0.82, 0.98)
    else:
        bg_light = rand.uniform(0.9, 0.98)
        text_light = rand.uniform(0.06, 0.18)
    bg_sat = rand.uniform(0.02, 0.12)
    bg_hex = hsl_to_hex(bg_hue, bg_sat, bg_light)
    fg_hex = hsl_to_hex((bg_hue + 180) % 360, 0.0, text_light)

    primary_hue = rand.uniform(0, 360)
    hues = _choose_harmony_hues(rand, primary_hue)

    def role_color(hue, sat_range=(0.45, 0.9), light_range=(0.45, 0.7)):
        sat = rand.uniform(*sat_range)
        light = rand.uniform(*light_range) if is_dark else rand.uniform(0.25, 0.55)
        raw = hsl_to_hex(hue, sat, light)
        safe = _ensure_contrast(raw, bg_hex, _MIN_CONTRAST)
        return safe

    color_comment = role_color(hues[2], sat_range=(0.2, 0.45), light_range=(0.45, 0.6))
    color_keyword = role_color(hues[0], sat_range=(0.55, 0.95), light_range=(0.45, 0.7))
    color_func = role_color(hues[0], sat_range=(0.45, 0.9), light_range=(0.35, 0.6))
    color_builtin = role_color(hues[1], sat_range=(0.35, 0.75), light_range=(0.45, 0.7))
    color_string = role_color((hues[0]+60) % 360, sat_range=(0.45, 0.9), light_range=(0.4, 0.7))
    color_number = role_color((hues[1]+120) % 360, sat_range=(0.45, 0.9), light_range=(0.45, 0.7))
    color_literal = role_color((hues[2]+90) % 360, sat_range=(0.45, 0.9), light_range=(0.45, 0.7))
    color_generic = role_color((primary_hue+200) % 360, sat_range=(0.15, 0.5), light_range=(0.4, 0.7))

    line_number = _ensure_contrast(hsl_to_hex(bg_hue, 0.05, clamp01(bg_light + (0.12 if is_dark else -0.12))), bg_hex, 1.5)
    line_number_current = color_keyword

    styles = {
        Comment: f"italic {color_comment}",
        Keyword: f"bold {color_keyword}",
        Keyword.Declaration: f"bold {color_keyword}",
        Name: fg_hex,
        Name.Function: color_func,
        Name.Builtin: color_builtin,
        Name.Decorator: color_keyword,
        Name.Class: color_builtin,
        String: color_string,
        Number: color_number,
        Operator: fg_hex,
        Literal: color_literal,
        Generic: color_generic,
        Token.LineNumber: line_number,
        Token.LineNumber.Current: f"bold {line_number_current}",
        Text: fg_hex,
    }

    cls_name = f"RandomTheme_{seed or rand.randint(0, 10**9)}"
    attrs = {"background_color": bg_hex, "default_style": fg_hex, "styles": styles}
    StyleClass = type(cls_name, (Style,), attrs)
    return StyleClass, bg_hex

# ---------- Public helper ----------
def get_syntax_theme(name: str):
    """
    Returns (PygmentsStyleClass, background_hex).

    Behaviour:
      - "random" -> new ephemeral random theme
      - "random:<seed>" or "r:<seed>" -> deterministic by seed (accepts int or string)
      - otherwise: look up THEME_MAP (case-insensitive)
      - default fallback: OneDarkStyle
    """
    if not name:
        return THEME_MAP["one_dark"]

    lname = name.lower()
    if lname == "random":
        cls, bg = generate_random_theme(seed=None, prefer_dark=True)
        return cls, bg

    for prefix in ("random:", "rand:", "r:"):
        if lname.startswith(prefix):
            seed_part = name.split(":", 1)[1]
            try:
                seed_val = int(seed_part)
            except Exception:
                seed_val = abs(hash(seed_part)) % (1 << 30)
            cache_key = f"random:{seed_val}"
            if cache_key in _RANDOM_THEME_CACHE:
                return _RANDOM_THEME_CACHE[cache_key]
            cls, bg = generate_random_theme(seed=seed_val, prefer_dark=True)
            _RANDOM_THEME_CACHE[cache_key] = (cls, bg)
            return cls, bg

    # exact / case-insensitive lookup
    if name in THEME_MAP:
        return THEME_MAP[name]
    for k in THEME_MAP:
        if k.lower() == name.lower():
            return THEME_MAP[k]

    # fallback
    return THEME_MAP["one_dark"]

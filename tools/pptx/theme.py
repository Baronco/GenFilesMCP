"""Color and theme resolution utilities for the PPTX slide generator."""

import colorsys
from typing import Optional

from pptx.dml.color import RGBColor

from tools.pptx.models import StyleOverride, Theme


def hex_to_rgb(value: str) -> RGBColor:
    """Convert a CSS hex color string to a pptx RGBColor."""
    v = value.lstrip("#")
    return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def _resolve_background(theme: Theme, background: str):
    """Resolve a background token to (bg_rgb, txt_color)."""
    if background == "accent_color":
        bg_rgb = hex_to_rgb(theme.accent_color)
    else:
        bg_rgb = hex_to_rgb(theme.background_color)
    r, g, b = int(bg_rgb[0]), int(bg_rgb[1]), int(bg_rgb[2])
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    txt_color = RGBColor(255, 255, 255) if luminance < 0.5 else RGBColor(30, 30, 30)
    return bg_rgb, txt_color


def _resolve_slide_background(theme: Theme, override: Optional[StyleOverride]):
    """Every slide uses the theme background for a fully cohesive deck."""
    return _resolve_background(theme, "background_color")


def _resolve_header_bar(override: Optional[StyleOverride], default: bool = True) -> bool:
    """Resolve a slide's effective header_bar flag, honoring an optional style_override."""
    if override is not None and override.header_bar is not None:
        return override.header_bar
    return default


def _relative_luminance(c: RGBColor) -> float:
    """WCAG relative luminance (gamma-corrected)."""
    def _lin(v: float) -> float:
        v = int(v) / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(c[0]) + 0.7152 * _lin(c[1]) + 0.0722 * _lin(c[2])


def _wcag_contrast(c1: RGBColor, c2: RGBColor) -> float:
    """WCAG contrast ratio between two colors (1.0 = none, 21.0 = black/white)."""
    l1, l2 = _relative_luminance(c1), _relative_luminance(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _blend_color(c1: RGBColor, c2: RGBColor, t: float) -> RGBColor:
    """Linear-interpolate between two colors. t=0 -> c1, t=1 -> c2."""
    return RGBColor(
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _scale_lightness(rgb: RGBColor, factor: float) -> RGBColor:
    """Scale a color's lightness by `factor`, keeping its hue and saturation."""
    h, l, s = colorsys.rgb_to_hls(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
    l = max(0.16, min(0.90, l * factor))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return RGBColor(int(r * 255), int(g * 255), int(b * 255))


def _impact_gradient(theme: Theme, variant: int = 0):
    """Return (color1, color2, angle, text_color) gradient used on all impact slides."""
    accent = hex_to_rgb(theme.accent_color)
    grad = hex_to_rgb(theme.gradient_accent)
    bg = hex_to_rgb(theme.background_color)
    white, black = RGBColor(255, 255, 255), RGBColor(20, 20, 20)
    dark_theme = _relative_luminance(bg) < 0.2

    def min_contrast(t):
        """Return the lower WCAG contrast ratio of t against both gradient stops."""
        return min(_wcag_contrast(t, c1), _wcag_contrast(t, c2))

    if dark_theme:
        c1, c2 = _scale_lightness(accent, 0.72), _scale_lightness(grad, 0.62)
        use_white = True
    else:
        c1, c2 = accent, grad
        use_white = min_contrast(white) >= min_contrast(black)

    text = white if use_white else black
    factor = 0.9 if use_white else 1.12
    for _ in range(14):
        if min_contrast(text) >= 4.5:
            break
        c1, c2 = _scale_lightness(c1, factor), _scale_lightness(c2, factor)
    return c1, c2, 55.0, text


def _header_fill(accent_rgb: RGBColor) -> RGBColor:
    """Fill color for header bars / column-title chips, guaranteed WCAG-legible against white."""
    fill = accent_rgb
    white = RGBColor(255, 255, 255)
    for _ in range(10):
        if _wcag_contrast(fill, white) >= 4.5:
            break
        fill = _scale_lightness(fill, 0.82)
    return fill


def _accent_on(accent_rgb: RGBColor, bg_rgb: RGBColor, target: float = 4.5) -> RGBColor:
    """Accent color safe to draw as foreground on bg_rgb, darkened until WCAG target is met."""
    factor = 0.85 if _relative_luminance(bg_rgb) > 0.4 else 1.18
    fg = accent_rgb
    for _ in range(14):
        if _wcag_contrast(fg, bg_rgb) >= target:
            break
        fg = _scale_lightness(fg, factor)
    return fg


def _contrast_text_color(*colors: RGBColor) -> RGBColor:
    """Contrasting text color (white or near-black) for one or more background colors."""
    def _luminance(c: RGBColor) -> float:
        r, g, b = int(c[0]), int(c[1]), int(c[2])
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    avg = sum(_luminance(c) for c in colors) / len(colors)
    return RGBColor(255, 255, 255) if avg < 0.55 else RGBColor(30, 30, 30)

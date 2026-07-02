"""Pydantic models and type aliases for the PPTX slide generator."""

import colorsys
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

from utils.config.logger import get_logger

logger = get_logger(__name__)

# Accepts theme tokens or an explicit hex color (#RRGGBB)
BackgroundField = Union[
    Literal["accent_color", "background_color"],
    Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")],
]

TextStyle = Literal["prose", "bullets"]

#: The executive-core chart types reachable from the YAML `chart_type` field.
EXECUTIVE_CHART_TYPES = {
    "bar", "stacked_bar", "stacked_bar_100", "line", "area", "stacked_area",
    "pie", "doughnut", "scatter", "bubble", "combo", "waterfall", "hist",
}


class Theme(BaseModel):
    """A named, curated bundle of visual choices applied to an entire presentation."""
    accent_color: str
    gradient_accent: str
    background_color: str
    font_heading: str
    font_body: str
    chart_palette: str


def _derive_palette(base_hex: str, mode: str):
    """Derive a coherent (accent, gradient_accent, background) triple from a single base hue."""
    v = base_hex.lstrip("#")
    r, g, b = int(v[0:2], 16) / 255, int(v[2:4], 16) / 255, int(v[4:6], 16) / 255
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    s = min(max(s, 0.32), 0.50)

    def hx(light: float, sat: float) -> str:
        """Convert HLS lightness/saturation to a CSS hex string using the palette hue."""
        rr, gg, bb = colorsys.hls_to_rgb(h, max(0.0, min(1.0, light)), max(0.0, min(1.0, sat)))
        return "#{:02X}{:02X}{:02X}".format(int(rr * 255), int(gg * 255), int(bb * 255))

    if mode == "dark":
        return hx(0.64, s), hx(0.42, s), hx(0.12, min(s * 0.12, 0.07))
    return hx(0.42, s), hx(0.66, s), hx(0.974, min(s * 0.07, 0.035))


def _theme_from_base(base_hex: str, mode: str, font: str, chart_palette: str) -> Theme:
    """Build a Theme from a single base hue, deriving a coherent accent/gradient/background triple."""
    accent, gradient, bg = _derive_palette(base_hex, mode)
    return Theme(accent_color=accent, gradient_accent=gradient, background_color=bg,
                 font_heading="Segoe UI Semibold", font_body="Segoe UI", chart_palette=chart_palette)


THEME_CATALOG: dict = {
    "corporate_blue": _theme_from_base("#1E6FD0", "light", "Calibri", "Blues"),
    "warm_editorial": _theme_from_base("#E0612F", "light", "Calibri", "Oranges"),
    "minimal_mono":   _theme_from_base("#475569", "light", "Calibri", "Greys"),
    "vibrant_teal":   _theme_from_base("#0D9488", "light", "Calibri", "Greens"),
    "royal_purple":   _theme_from_base("#7C3AED", "light", "Calibri", "Purples"),
    "crimson_report": _theme_from_base("#C2333A", "light", "Calibri", "Reds"),
    "forest_green":   _theme_from_base("#15803D", "light", "Calibri", "Greens"),
    "amber_gold":     _theme_from_base("#B7791F", "light", "Calibri", "YlOrBr"),
    "modern_dark":    _theme_from_base("#3B82F6", "light", "Calibri", "Blues"),
    "emerald_dark":   _theme_from_base("#10B981", "light", "Calibri", "Greens"),
    "graphite_dark":  _theme_from_base("#33566E", "light", "Calibri", "Greys"),
}
DEFAULT_THEME = "corporate_blue"


class StyleOverride(BaseModel):
    """Optional, explicit visual choice for a single slide, layered over the active theme."""
    background: Optional[BackgroundField] = None
    header_bar: Optional[bool] = None


class CoverSlide(BaseModel):
    type: Literal["cover"] = "cover"
    title: str
    subtitle: Optional[str] = ""
    date: Optional[str] = ""
    notes: Optional[str] = None


class ContentImageSlide(BaseModel):
    type: Literal["content_image"] = "content_image"
    title: str
    text: str
    image_id: str
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None


class TwoColumnSide(BaseModel):
    title: str
    text: str


class TwoColumnSlide(BaseModel):
    type: Literal["two_column"] = "two_column"
    title: str
    left: TwoColumnSide
    right: TwoColumnSide
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None


class SectionDividerSlide(BaseModel):
    type: Literal["section_divider"] = "section_divider"
    title: str
    subtitle: Optional[str] = ""
    notes: Optional[str] = None


class ContentTextSlide(BaseModel):
    type: Literal["content_text"] = "content_text"
    title: str
    text: str
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None


class ChartSeries(BaseModel):
    """One named data series sharing a chart's category/X axis."""
    name: str
    values: List[float]
    kind: Optional[Literal["bar", "line", "area"]] = None
    axis: Optional[Literal["primary", "secondary"]] = "primary"


class ChartData(BaseModel):
    """A chart expressed as one of four visualization intents."""
    intent: Literal["comparison", "trend", "distribution", "part_of_whole"]
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    values: Optional[List[float]] = None
    x: Optional[List[float]] = None
    y: Optional[List[float]] = None
    chart_type: Optional[str] = None
    series: Optional[List[ChartSeries]] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    y2_label: Optional[str] = None
    value_labels: Optional[bool] = None
    legend: Optional[bool] = None
    value_format: Optional[Literal[
        "auto", "int", "float1", "percent", "thousands", "currency",
    ]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_intent(cls, data):
        """Normalize intent; when intent is a chart_type or unknown, infer from data shape."""
        if not isinstance(data, dict):
            return data
        valid = {"comparison", "trend", "distribution", "part_of_whole"}
        intent = data.get("intent")
        if isinstance(intent, str) and intent.strip().lower() in valid:
            data["intent"] = intent.strip().lower()
            return data
        v = intent.strip().lower() if isinstance(intent, str) else None
        if v and v in EXECUTIVE_CHART_TYPES:
            data.setdefault("chart_type", v)
        ct = (data.get("chart_type") or "").strip().lower()
        if data.get("x") and data.get("y"):
            data["intent"] = "trend"
        elif ct in ("pie", "doughnut"):
            data["intent"] = "part_of_whole"
        elif ct == "hist":
            data["intent"] = "distribution"
        elif data.get("categories") and (data.get("values") or data.get("series")):
            data["intent"] = "comparison"
        elif data.get("values") or data.get("series"):
            data["intent"] = "comparison"
        else:
            data["intent"] = "comparison"
        if intent is not None and str(intent).strip().lower() != data["intent"]:
            logger.warning("chart.intent '%s' coerced to '%s' (chart_type=%s).",
                           intent, data["intent"], data.get("chart_type") or "default")
        return data

    @model_validator(mode="after")
    def validate_chart(self):
        """Validate and normalise chart_type and data requirements."""
        if self.chart_type:
            ct = self.chart_type.strip().lower()
            if ct not in EXECUTIVE_CHART_TYPES:
                logger.warning("Unknown chart_type '%s'; using the intent default instead.", self.chart_type)
                self.chart_type = None
            else:
                self.chart_type = ct
        has_series = bool(self.series)
        if self.intent in ("comparison", "part_of_whole"):
            if not (self.values or has_series):
                raise ValueError(f"'{self.intent}' charts require 'categories' and 'values'.")
            if self.values and self.categories and len(self.categories) != len(self.values):
                min_len = min(len(self.categories), len(self.values))
                self.categories = self.categories[:min_len]
                self.values = self.values[:min_len]
        elif self.intent == "trend":
            if not ((self.x and self.y) or has_series or (self.x and self.values)):
                raise ValueError("'trend' charts require 'x' and 'y'.")
            if self.x and self.y and len(self.x) != len(self.y):
                min_len = min(len(self.x), len(self.y))
                self.x = self.x[:min_len]
                self.y = self.y[:min_len]
        elif self.intent == "distribution":
            if not (self.values or has_series):
                raise ValueError("'distribution' charts require 'values'.")
        return self


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]


class ContentMixedSlide(BaseModel):
    type: Literal["content_mixed"] = "content_mixed"
    title: str
    text: Optional[str] = None
    image_id: Optional[str] = None
    chart: Optional[ChartData] = None
    table: Optional[TableData] = None
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_contents(self):
        """Keep only one visual element, preferring chart > table > image_id."""
        contents = [bool(self.image_id), bool(self.chart), bool(self.table)]
        if sum(contents) > 1:
            logger.warning(
                "content_mixed slide '%s' has %d visual element(s). Keeping only one.",
                self.title, sum(contents),
            )
            if self.chart and self.image_id:
                logger.warning("  -> Dropped image_id in favour of chart.")
                self.image_id = None
            elif self.chart and self.table:
                logger.warning("  -> Dropped table in favour of chart.")
                self.table = None
            elif self.table and self.image_id:
                logger.warning("  -> Dropped image_id in favour of table.")
                self.image_id = None
        elif sum(contents) == 0:
            logger.warning(
                "content_mixed slide '%s' has no visual element. Defaulting to text-only.",
                self.title,
            )
        return self


class TimelineEvent(BaseModel):
    fecha: str
    titulo: str
    emoji: Optional[str] = None


class TimelineSlide(BaseModel):
    type: Literal["timeline"] = "timeline"
    title: str
    items: List[TimelineEvent]
    active_index: Optional[int] = None
    style: Literal["horizontal", "vertical"] = "horizontal"
    image_id: Optional[str] = None
    text: Optional[str] = None
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_items(self):
        """Ensure at least two timeline items and a valid active_index."""
        if not self.items or len(self.items) < 2:
            raise ValueError("timeline requires at least two items.")
        if self.active_index is not None and not (0 <= self.active_index < len(self.items)):
            raise ValueError("timeline.active_index must refer to a valid item index.")
        return self


class ContentLatexSlide(BaseModel):
    type: Literal["content_latex"] = "content_latex"
    layout: Literal["full", "split"] = "split"
    title: str
    text: Optional[str] = None
    latex_lines: List[str] = Field(
        ...,
        description=(
            "Ordered list of mathtext strings to render as a stacked image. "
            "Wrap equations in $...$, e.g. '$E = mc^2$'. "
            "Use '$\\bullet\\;$' prefix for bullet-style items."
        ),
    )
    image_id: Optional[str] = None
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None


class StatHighlightSlide(BaseModel):
    """Spotlights a single key figure/metric with a high-impact gradient treatment."""
    type: Literal["stat_highlight"] = "stat_highlight"
    value: str
    label: str
    supporting_text: Optional[str] = None
    style_override: Optional[StyleOverride] = None
    notes: Optional[str] = None


Slide = Annotated[
    CoverSlide | ContentImageSlide | ContentMixedSlide | ContentLatexSlide | ContentTextSlide | TimelineSlide | TwoColumnSlide | SectionDividerSlide | StatHighlightSlide,
    Field(discriminator="type"),
]


class PresentationDefinition(BaseModel):
    theme: str = DEFAULT_THEME
    slides: List[Slide]

    @model_validator(mode="after")
    def validate_theme(self):
        """Fall back to the default theme if the requested one is unrecognized."""
        if self.theme not in THEME_CATALOG:
            logger.warning(
                "Unrecognized theme '%s'; falling back to default theme '%s'.",
                self.theme, DEFAULT_THEME,
            )
            self.theme = DEFAULT_THEME
        return self

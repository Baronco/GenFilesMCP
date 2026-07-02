"""Chart rendering utilities: executive charts, LaTeX equation images, image registry."""

import re as _re
from io import BytesIO

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from tools.pptx.models import ChartData, EXECUTIVE_CHART_TYPES
from tools.pptx.seaborn import slide_chart
from tools.pptx.shapes import place_image_centered
from tools.pptx.text import _LATEX_CMD_TO_UNICODE, _sanitize_latex_line, add_text_box
from tools.pptx.theme import _accent_on
from utils.config.logger import get_logger

logger = get_logger(__name__)

_INTENT_TO_CHART_KIND = {
    "comparison": "bar",
    "trend": "line",
    "distribution": "hist",
    "part_of_whole": "pie",
}

#: Chart types that need numeric X and Y (a category axis can't drive them).
_NEEDS_NUMERIC_XY = {"scatter", "bubble"}


def _resolve_chart_type(chart_def: ChartData) -> str:
    """Resolve the effective executive chart type: an explicit, compatible `chart_type`
    wins; otherwise fall back to the intent default. Unknown or data-incompatible types
    degrade gracefully (intent default) with a warning so a single chart never fails the
    deck (FR-014)."""
    default = _INTENT_TO_CHART_KIND[chart_def.intent]
    ct = chart_def.chart_type
    if not ct:
        return default
    if ct not in EXECUTIVE_CHART_TYPES:
        logger.warning("Unknown chart_type '%s'; falling back to intent default '%s'.", ct, default)
        return default
    if ct in _NEEDS_NUMERIC_XY and not (chart_def.x and chart_def.y):
        logger.warning("chart_type '%s' needs numeric x and y; falling back to '%s'.", ct, default)
        return default
    return ct


def _chart_series(chart_def: ChartData) -> list:
    """Normalize a ChartData into a list of {name, values, kind, axis} series, aligned to
    the shared category/X axis. Multiple `series` win; otherwise a single series is built
    from `values`/`y`. Lengths are aligned/truncated, never rejected (FR-010)."""
    axis_len = None
    if chart_def.categories is not None:
        axis_len = len(chart_def.categories)
    elif chart_def.x is not None:
        axis_len = len(chart_def.x)
    elif chart_def.series:
        axis_len = max((len(s.values) for s in chart_def.series), default=0)

    def _clip(vals):
        if axis_len is None or vals is None:
            return vals
        if len(vals) >= axis_len:
            return vals[:axis_len]
        return list(vals) + [0.0] * (axis_len - len(vals))

    if chart_def.series:
        return [{"name": s.name, "values": _clip(list(s.values)),
                 "kind": s.kind, "axis": s.axis} for s in chart_def.series]
    single = chart_def.values if chart_def.values is not None else chart_def.y
    return [{"name": "", "values": _clip(list(single or []))}]


def _render_chart_image(chart_def: ChartData, palette: str, width, height):
    """Render a chart for a slide via the executive renderer. The theme's chart_palette is
    always applied. Falls back to a plain bar/line chart if the executive renderer fails."""
    from matplotlib import pyplot as plt

    chart_type = _resolve_chart_type(chart_def)
    series = _chart_series(chart_def)
    labels = chart_def.categories
    x = chart_def.x
    sizes = chart_def.values if chart_type == "bubble" else None

    buf = BytesIO()
    try:
        result = slide_chart(
            chart_type,
            palette=palette,
            title=chart_def.title or "",
            labels=labels,
            x=x,
            series=series,
            sizes=sizes,
            x_label=chart_def.x_label or "",
            y_label=chart_def.y_label or "",
            y2_label=chart_def.y2_label or "",
            value_labels=chart_def.value_labels,
            legend=chart_def.legend,
            value_format=chart_def.value_format,
            save_path=buf,
        )
    except Exception as exc:
        logger.warning("Executive chart '%s' failed (%s); rendering a safe fallback.", chart_type, exc)
        plt.close("all")
        buf = BytesIO()
        fallback = "line" if chart_def.intent == "trend" else "bar"
        result = slide_chart(
            fallback, palette=palette, title=chart_def.title or "",
            labels=labels, x=x, series=_chart_series(chart_def), save_path=buf,
        )

    if isinstance(result, tuple):
        fig = result[0]
        plt.close(fig if isinstance(fig, plt.Figure) else "all")
    elif isinstance(result, plt.Figure):
        plt.close(result)
    else:
        plt.close("all")

    buf.seek(0)
    return buf


def add_chart(slide, chart_def: ChartData, palette: str, left, top, width, height,
              accent_rgb: RGBColor = None, bg_rgb: RGBColor = None,
              txt_color: RGBColor = None):
    """Render charts using the matplotlib backend and insert the image into PowerPoint.
    The chart is placed on a white rounded card with a thin themed border so it reads as
    an intentionally placed element rather than a stray white rectangle, especially on
    dark or strongly colored themes (the matplotlib backend always renders on white)."""
    try:
        chart_image = _render_chart_image(chart_def, palette, width, height)
        pad = Inches(0.12)
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            int(left - pad), int(top - pad), int(width + 2 * pad), int(height + 2 * pad),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        card.line.color.rgb = _accent_on(accent_rgb, RGBColor(255, 255, 255)) if accent_rgb else RGBColor(200, 200, 200)
        card.line.width = Pt(0.75)
        card.shadow.inherit = False
        try:
            card.adjustments[0] = 0.04
        except (IndexError, ValueError):
            pass
        place_image_centered(slide, chart_image, left, top, width, height)
    except Exception as e:
        logger.warning("Chart rendering failed: %s. Adding placeholder text instead.", e)
        add_text_box(slide, left, top, width, height,
                     f"[Chart could not be rendered: {e}]",
                     "Calibri", 12, color=txt_color or RGBColor(180, 180, 180),
                     align=PP_ALIGN.LEFT)
    return


def _render_latex_to_image(
    latex_lines: list,
    bg_rgb: RGBColor,
    txt_rgb: RGBColor,
    dpi: int = 300,
) -> BytesIO:
    """Render a list of mathtext strings to a transparent PNG image in memory."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fg = (txt_rgb[0] / 255, txt_rgb[1] / 255, txt_rgb[2] / 255)
    sanitized_lines = [_sanitize_latex_line(raw_line).strip() for raw_line in latex_lines] or ['']
    weights = [
        1.5 if any(marker in line for marker in (r'\sum', r'\prod', r'\int', r'\frac', r'\sqrt'))
        else 1.0
        for line in sanitized_lines
    ]
    total_weight = sum(weights)
    fig_h = max(1.5, total_weight * 0.95)
    fig, ax = plt.subplots(figsize=(10, fig_h), dpi=dpi)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    from matplotlib import mathtext as _mathtext
    _math_parser = _mathtext.MathTextParser('path')

    def _to_plain(s: str) -> str:
        s = _re.sub(r'\$', '', s)
        for _cmd, _uni in _LATEX_CMD_TO_UNICODE.items():
            s = s.replace(_cmd, _uni)
        s = _re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', s)
        s = _re.sub(r'\\[a-zA-Z]+', '', s)
        return s.replace('{', '').replace('}', '').strip()

    def _math_ok(s: str) -> bool:
        try:
            _math_parser.parse(s)
            return True
        except Exception:
            return False

    def _draw(plain_only: bool):
        cumulative = 0.0
        for line, weight in zip(sanitized_lines, weights):
            candidate = line
            if candidate and not (candidate.startswith('$') and candidate.endswith('$')):
                candidate = f'${candidate}$'
            y = 1.0 - (cumulative + weight / 2) / total_weight
            cumulative += weight
            if not plain_only and candidate and _math_ok(candidate):
                ax.text(0.02, y, candidate, transform=ax.transAxes, fontsize=18,
                        color=fg, verticalalignment='center', horizontalalignment='left')
            else:
                ax.text(0.02, y, _to_plain(line), transform=ax.transAxes, fontsize=18,
                        color=fg, verticalalignment='center', horizontalalignment='left',
                        parse_math=False)

    _draw(plain_only=False)
    buf = BytesIO()
    try:
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                    transparent=True, edgecolor='none')
    except Exception:
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        _draw(plain_only=True)
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight',
                    transparent=True, edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


def _resolve_image(image_registry: dict, image_id: str):
    image = image_registry.get(image_id)
    if image is None:
        raise FileNotFoundError(f"image_id '{image_id}' not found in registry.")
    if hasattr(image, "seek"):
        image.seek(0)
    return image

"""Slide shape drawing utilities: backgrounds, primitives, tables, images, header bar."""

from typing import Optional

from PIL import Image as PILImage
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from tools.pptx.models import TableData
from tools.pptx.text import add_text_box
from tools.pptx.theme import _accent_on, _blend_color, _contrast_text_color, _header_fill

MARGIN = Inches(0.75)
BAR_H = Inches(0.8)


def set_slide_background(slide, color: RGBColor):
    """Fill the slide background with a flat solid color."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _apply_gradient_background(slide, color1: RGBColor, color2: RGBColor, angle: float = 45.0):
    """Two-stop diagonal gradient background, used only on "impact" slides
    (cover, section_divider, stat_highlight) — never on ordinary content slides."""
    fill = slide.background.fill
    fill.gradient()
    stops = fill.gradient_stops
    stops[0].color.rgb = color1
    stops[0].position = 0.0
    stops[1].color.rgb = color2
    stops[1].position = 1.0
    fill.gradient_angle = angle


def add_rect(slide, x, y, w, h, fill_color, line_color=None, line_w_pt=0):
    """Add a filled rectangle shape; border omitted when line_color is None."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        int(round(x)), int(round(y)), int(round(w)), int(round(h))
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_w_pt)
    else:
        shape.line.fill.background()
    return shape


def add_oval_shape(slide, x, y, w, h, fill_color, line_color=None, line_w_pt=1.5):
    """Add an oval/ellipse shape; pass fill_color=None for a transparent fill."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        int(round(x)), int(round(y)), int(round(w)), int(round(h))
    )
    if fill_color is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_w_pt)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_line_shape(slide, x1, y1, x2, y2, color, width_pt=1.5, dash=False):
    """Add a straight connector line between two points; optionally dashed."""
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(width_pt)
    if dash:
        connector.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return connector


def add_table(slide, table_def: TableData, left, top, width, height, font_name,
              font_size: int = 11, accent_rgb: RGBColor = None,
              bg_rgb: RGBColor = None, txt_color: RGBColor = None,
              vertical_center: bool = False):
    """Add a styled table: accent-colored header row, alternating row backgrounds.
    vertical_center=True centers the table within the allotted `height` so it lines up with
    vertically-centered body text beside it (instead of hugging the top of its column)."""
    _accent = accent_rgb or RGBColor(0x0D, 0x94, 0x88)
    _header = _header_fill(_accent)
    _bg = bg_rgb or RGBColor(0xF0, 0xFD, 0xFA)
    _txt = txt_color or RGBColor(30, 30, 30)
    alt_rgb = RGBColor(
        min(255, int(_bg[0] * 0.93 + _accent[0] * 0.07)),
        min(255, int(_bg[1] * 0.93 + _accent[1] * 0.07)),
        min(255, int(_bg[2] * 0.93 + _accent[2] * 0.07)),
    )
    rows = len(table_def.rows) + 1
    cols = len(table_def.headers)
    row_height = Inches(0.40)
    actual_height = min(rows * row_height, height)
    if vertical_center and actual_height < height:
        top = int(top + (height - actual_height) / 2)
    tbl_shape = slide.shapes.add_table(rows, cols, left, top, width, actual_height)
    tbl = tbl_shape.table
    for ci, header in enumerate(table_def.headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _header
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.text = str(header)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
    for ri, row_data in enumerate(table_def.rows, start=1):
        row_bg = alt_rgb if ri % 2 == 0 else _bg
        for ci in range(cols):
            cell = tbl.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            cell_text = str(row_data[ci]) if ci < len(row_data) else ''
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.runs[0] if p.runs else p.add_run()
            run.text = cell_text
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = _txt
    return tbl_shape


def add_vertical_separator(slide, x, top, bottom, accent_rgb):
    """Draw a thin vertical accent line between two-column layouts."""
    sep = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, top, x, bottom)
    sep.line.width = Pt(1.5)
    sep.line.color.rgb = accent_rgb


def _add_notes(slide, text: Optional[str]) -> None:
    """Write presenter notes to the slide's notes pane."""
    if not text:
        return
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text


def place_image_centered(slide, img_source, left, top, max_width, max_height,
                          valign: str = "center", halign: str = "center"):
    """Place an image inside a bounding box, preserving aspect ratio and aligning it."""
    if hasattr(img_source, "seek"):
        img_source.seek(0)
    with PILImage.open(img_source) as im:
        img_w, img_h = im.size

    ratio = img_w / img_h
    if (max_width / max_height) >= ratio:
        final_h = max_height
        final_w = int(final_h * ratio)
    else:
        final_w = max_width
        final_h = int(final_w / ratio)

    if halign == "left":
        offset_x = 0
    elif halign == "right":
        offset_x = int(max_width - final_w)
    else:
        offset_x = int((max_width - final_w) / 2)

    if valign == "top":
        offset_y = 0
    elif valign == "bottom":
        offset_y = int(max_height - final_h)
    else:
        offset_y = int((max_height - final_h) / 2)

    if hasattr(img_source, "seek"):
        img_source.seek(0)
    picture = slide.shapes.add_picture(
        img_source,
        left + offset_x,
        top + offset_y,
        width=final_w,
        height=final_h,
    )
    return picture


def add_header_bar(slide, prs, title, font_name, accent_rgb, bg_rgb=None, txt_color=None,
                   bar_height=Inches(1.05), show_tab=True):
    """Light, editorial header: a short rounded accent tab + a dark, left-aligned title + a
    thin hairline rule beneath it. Replaces the old heavy full-width colored bar for a cleaner,
    more designed look. Works on any background (including a custom style_override panel): the
    title and hairline adapt to contrast. `show_tab=False` drops the accent tab (used when a
    slide hides the header bar) while keeping the same clean title + hairline so every slide
    looks consistent."""
    W = prs.slide_width
    bg = bg_rgb or RGBColor(255, 255, 255)
    title_color = txt_color or _contrast_text_color(bg)

    if show_tab:
        tab_color = _accent_on(accent_rgb, bg) if accent_rgb else RGBColor(90, 90, 90)
        tab_w, tab_h, tab_top = Inches(0.13), Inches(0.46), Inches(0.46)
        tab = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MARGIN, tab_top, tab_w, tab_h)
        tab.fill.solid()
        tab.fill.fore_color.rgb = tab_color
        tab.line.fill.background()
        tab.shadow.inherit = False
        try:
            tab.adjustments[0] = 0.5
        except (IndexError, ValueError):
            pass
        title_left = MARGIN + tab_w + Inches(0.24)
    else:
        title_left = MARGIN

    add_text_box(slide, title_left, Inches(0.34), W - title_left - MARGIN, Inches(0.74),
                 title, font_name, 27, bold=True, color=title_color, align=PP_ALIGN.LEFT,
                 word_wrap=False)

    rule_y = bar_height - Inches(0.07)
    add_rect(slide, MARGIN, rule_y, W - MARGIN * 2, Inches(0.012),
             fill_color=_blend_color(bg, title_color, 0.22))
    return bar_height

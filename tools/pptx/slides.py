"""Slide builder functions for each slide type in the PPTX generator."""

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from tools.pptx.charts import _render_latex_to_image, _resolve_image, add_chart
from tools.pptx.models import (
    ContentImageSlide,
    ContentLatexSlide,
    ContentMixedSlide,
    ContentTextSlide,
    CoverSlide,
    SectionDividerSlide,
    StatHighlightSlide,
    Theme,
    TimelineSlide,
    TwoColumnSlide,
)
from tools.pptx.shapes import (
    MARGIN,
    _add_notes,
    _apply_gradient_background,
    add_header_bar,
    add_oval_shape,
    add_rect,
    add_table,
    place_image_centered,
    set_slide_background,
)
from tools.pptx.text import add_text_box, sanitize_slide_text
from tools.pptx.theme import (
    _accent_on,
    _blend_color,
    _impact_gradient,
    _resolve_header_bar,
    _resolve_slide_background,
    hex_to_rgb,
)


def _add_accent_title_bar(slide, prs, title, font_name, accent_rgb, txt_color, header_bar, bg_rgb):
    """Unified title rendering. Returns content_top (position after the title area). Both
    variants share the same clean editorial header so every slide is consistent:
    - header_bar=True: accent tab + left title + hairline
    - header_bar=False: the same, minus the accent tab (a more minimal title)
    """
    return add_header_bar(slide, prs, title, font_name, accent_rgb,
                          bg_rgb=bg_rgb, txt_color=txt_color, show_tab=header_bar)


def build_cover(prs, theme: Theme, data: CoverSlide, image_registry: dict, variant: int = 0):
    """High-impact cover: a clean two-tone gradient whose hue varies per impact slide,
    with content vertically and horizontally centered. No decorative shapes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    c1, c2, angle, txt = _impact_gradient(theme, variant)
    _apply_gradient_background(slide, c1, c2, angle)
    W, H = prs.slide_width, prs.slide_height
    inner_x = MARGIN + Inches(0.5)
    inner_w = W - inner_x - MARGIN - Inches(0.5)

    KICK_H = Inches(0.085)
    TITLE_H = Inches(1.9)
    SUB_H = Inches(0.6) if data.subtitle else Inches(0)
    DATE_H = Inches(0.4) if data.date else Inches(0)
    GAP_KT = Inches(0.34)
    GAP_TS = Inches(0.30) if data.subtitle else Inches(0)
    GAP_SD = Inches(0.22) if data.date else Inches(0)
    block_h = KICK_H + GAP_KT + TITLE_H + GAP_TS + SUB_H + GAP_SD + DATE_H
    block_top = int((H - block_h) / 2)

    add_rect(slide, inner_x, block_top, Inches(0.95), KICK_H, fill_color=txt)
    y = block_top + KICK_H + GAP_KT
    add_text_box(slide, inner_x, y, inner_w, TITLE_H,
                 data.title, theme.font_heading, 48,
                 bold=True, color=txt, align=PP_ALIGN.LEFT, word_wrap=True)
    y += TITLE_H + GAP_TS
    if data.subtitle:
        add_text_box(slide, inner_x, y, inner_w, SUB_H,
                     data.subtitle, theme.font_body, 22,
                     color=txt, align=PP_ALIGN.LEFT)
        y += SUB_H + GAP_SD
    if data.date:
        add_text_box(slide, inner_x, y, inner_w, DATE_H,
                     data.date, theme.font_body, 14,
                     color=txt, align=PP_ALIGN.LEFT)
    _add_notes(slide, data.notes)


def build_content_image(prs, theme: Theme, data: ContentImageSlide, image_registry: dict, variant: int = 0):
    """Left-text / Right-image layout."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    gutter = Inches(0.4)
    text_col_w = int((W - MARGIN * 2 - gutter) * 0.42)
    img_col_w = int((W - MARGIN * 2 - gutter) * 0.58)
    add_text_box(slide, MARGIN, content_top, text_col_w, content_h,
                 sanitize_slide_text(data.text, preserve_markdown=True), theme.font_body, 17,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 vertical_center=True, autofit=True)
    img_x = MARGIN + text_col_w + gutter
    img_source = _resolve_image(image_registry, data.image_id)
    place_image_centered(slide, img_source, img_x, content_top + Inches(0.1), img_col_w, content_h - Inches(0.2))
    _add_notes(slide, data.notes)


def build_two_column(prs, theme: Theme, data: TwoColumnSlide, image_registry: dict, variant: int = 0):
    """Build a side-by-side two-column slide with titled body columns."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    gutter = Inches(0.5)
    col_w = int((W - MARGIN * 2 - gutter) / 2)
    _build_column(slide, MARGIN, content_top, col_w, content_h,
                  sanitize_slide_text(data.left.title), data.left.text,
                  theme.font_heading, theme.font_body, txt_color, accent, bg_rgb)
    _build_column(slide, MARGIN + col_w + gutter, content_top, col_w, content_h,
                  sanitize_slide_text(data.right.title), data.right.text,
                  theme.font_heading, theme.font_body, txt_color, accent, bg_rgb)
    _add_notes(slide, data.notes)


def _build_column(slide, left, top, width, height,
                  title, text, font_heading, font_body, txt_color, accent, bg_rgb=None):
    """Render a single column: a left-aligned accent column title with a short underline rule
    (light/editorial — matches the new header treatment, no heavy solid colored chip), then
    top-aligned body text."""
    title_h = Inches(0.46)
    accent_fg = _accent_on(accent, bg_rgb or RGBColor(255, 255, 255))
    add_text_box(slide, left, top, width, title_h,
                 title, font_heading, 16,
                 bold=True, color=accent_fg, align=PP_ALIGN.LEFT)
    add_rect(slide, left, top + title_h, Inches(0.72), Inches(0.035), fill_color=accent_fg)
    body_top = top + title_h + Inches(0.20)
    body_h = height - title_h - Inches(0.20)
    add_text_box(slide, left, body_top, width, body_h,
                 sanitize_slide_text(text, preserve_markdown=True), font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 vertical_center=False, autofit=True)


def build_content_mixed(prs, theme: Theme, data: ContentMixedSlide, image_registry: dict, variant: int = 0):
    """Build a mixed-content slide: body text on the left, chart/image/table on the right."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    gutter = Inches(0.4)
    total_inner_w = W - MARGIN * 2 - gutter
    text_col_w = int(total_inner_w * 0.38)
    right_col_w = total_inner_w - text_col_w
    add_text_box(slide, MARGIN, content_top, text_col_w, H - content_top - MARGIN,
                 sanitize_slide_text(data.text or '', preserve_markdown=True), theme.font_body, 17,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 accent_rgb=accent, bg_rgb=bg_rgb, vertical_center=True, autofit=True)
    right_x = MARGIN + text_col_w + gutter
    if data.image_id:
        img_source = _resolve_image(image_registry, data.image_id)
        img_top = content_top + Inches(0.08)
        img_height = H - content_top - MARGIN - Inches(0.16)
        place_image_centered(slide, img_source, right_x, img_top, right_col_w, img_height)
    elif data.chart:
        add_chart(slide, data.chart, theme.chart_palette, right_x, content_top, right_col_w, H - content_top - MARGIN,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color)
    elif data.table:
        add_table(slide, data.table, right_x, content_top + Inches(0.1), right_col_w,
                  H - content_top - MARGIN - Inches(0.1), theme.font_body,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color, vertical_center=True)
    _add_notes(slide, data.notes)


def build_timeline(prs, theme: Theme, data: TimelineSlide, image_registry: dict, variant: int = 0):
    """Dispatch to vertical or horizontal timeline builder based on data.style."""
    if data.style == "vertical":
        return _build_timeline_vertical(prs, theme, data, image_registry)
    return _build_timeline_horizontal(prs, theme, data)


def _rail_tint(bg_rgb, accent_fg) -> RGBColor:
    """Soft accent-tinted rail/axis color — visible but quiet against the near-white slide."""
    return _blend_color(bg_rgb, accent_fg, 0.32)


def _draw_numbered_node(slide, cx, cy, number, accent_fg, bg_rgb, font_name, active: bool):
    """A filled accent circle with the step number in white. The active step is larger and
    gets a soft hollow outer ring so the current milestone stands out."""
    r = Inches(0.215) if active else Inches(0.185)
    if active:
        ring_r = r + Inches(0.085)
        add_oval_shape(slide, int(cx - ring_r), int(cy - ring_r), int(ring_r * 2), int(ring_r * 2),
                       fill_color=None, line_color=accent_fg, line_w_pt=1.5)
    add_oval_shape(slide, int(cx - r), int(cy - r), int(r * 2), int(r * 2),
                   fill_color=accent_fg, line_color=None)
    box = int(r * 2)
    add_text_box(slide, int(cx - r), int(cy - r), box, box, str(number),
                 font_name, 13 if active else 12, bold=True, color=RGBColor(255, 255, 255),
                 align=PP_ALIGN.CENTER, vertical_center=True)


def _event_card(slide, left, top, w, h, fecha, titulo, accent_fg, bg_rgb, txt_color,
                font_body, active: bool, center: bool = False, title_size: int = 14):
    """A rounded event card: a faint accent-tinted panel holding the date as a small accent
    label above a bold title. The active card is tinted/bordered a touch stronger. The title
    auto-fits inside the card so long milestone text never clips."""
    fill = _blend_color(bg_rgb, accent_fg, 0.11 if active else 0.05)
    border = accent_fg if active else _blend_color(bg_rgb, RGBColor(120, 120, 135), 0.32)
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, int(left), int(top), int(w), int(h))
    card.fill.solid()
    card.fill.fore_color.rgb = fill
    card.line.color.rgb = border
    card.line.width = Pt(1.5 if active else 0.75)
    card.shadow.inherit = False
    try:
        card.adjustments[0] = 0.09
    except (IndexError, ValueError):
        pass
    align = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    pad = Inches(0.16)
    date_h = Inches(0.22)
    add_text_box(slide, int(left + pad), int(top + Inches(0.11)), int(w - 2 * pad), int(date_h),
                 fecha, font_body, 11, color=accent_fg, bold=True, align=align)
    title_top = int(top + Inches(0.11) + date_h + Inches(0.02))
    title_h = int(top + h - Inches(0.12) - title_top)
    add_text_box(slide, int(left + pad), title_top, int(w - 2 * pad), max(title_h, int(Inches(0.3))),
                 titulo, font_body, title_size, color=txt_color, bold=True, align=align,
                 word_wrap=True, vertical_center=True, autofit=True)


def _build_timeline_horizontal(prs, theme: Theme, data: TimelineSlide):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    accent_fg = _accent_on(accent, bg_rgb)
    rail_rgb = _rail_tint(bg_rgb, accent_fg)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)

    items = data.items
    n_items = len(items)
    active_idx = data.active_index if data.active_index is not None else -1
    inset = Inches(1.3)
    axis_left = MARGIN + inset
    axis_right = W - MARGIN - inset
    step = (axis_right - axis_left) / max(n_items - 1, 1)

    line_y = int(round(content_top + (H - content_top - MARGIN) / 2))
    add_rect(slide, int(axis_left), line_y - int(Inches(0.014)), int(axis_right - axis_left), Inches(0.028),
             fill_color=rail_rgb)

    tw = Inches(2.5)
    date_h = Inches(0.24)
    title_h = Inches(0.62)
    block_h = date_h + Inches(0.04) + title_h
    node_gap = Inches(0.42)
    title_size = 14 if n_items <= 4 else 13
    for i, item in enumerate(items):
        x = int(round(axis_left + i * step))
        active = (i == active_idx)
        is_top = (i % 2 == 0)
        text_left = int(max(MARGIN, min(W - MARGIN - tw, x - tw / 2)))
        if is_top:
            block_top = int(line_y - node_gap - block_h)
        else:
            block_top = int(line_y + node_gap)
        add_text_box(slide, text_left, block_top, int(tw), int(date_h),
                     item.fecha, theme.font_body, 11, color=accent_fg, bold=True, align=PP_ALIGN.CENTER)
        add_text_box(slide, text_left, int(block_top + date_h + Inches(0.04)), int(tw), int(title_h),
                     item.titulo, theme.font_body, title_size, color=txt_color, bold=True,
                     align=PP_ALIGN.CENTER, word_wrap=True, autofit=True)
        _draw_numbered_node(slide, x, line_y, i + 1, accent_fg, bg_rgb, theme.font_heading, active)

    _add_notes(slide, data.notes)


def _build_timeline_vertical(prs, theme: Theme, data: TimelineSlide, image_registry: dict):
    """Vertical timeline: a top-to-bottom accent rail with numbered nodes, each event rendered
    as a card (date label + bold title) to its right. With an optional `image_id`/`text`, that
    content fills the LEFT side and the rail+cards shift to the RIGHT half."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    accent_fg = _accent_on(accent, bg_rgb)
    rail_rgb = _rail_tint(bg_rgb, accent_fg)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN

    has_side = bool(data.image_id or data.text)
    if has_side:
        gutter = Inches(0.5)
        left_w = int((W - MARGIN * 2 - gutter) * 0.46)
        rail_zone_left = MARGIN + left_w + gutter
        if data.image_id:
            img_source = _resolve_image(image_registry, data.image_id)
            place_image_centered(slide, img_source, MARGIN, content_top, left_w, content_h)
        elif data.text:
            add_text_box(slide, MARGIN, content_top, left_w, content_h,
                         sanitize_slide_text(data.text, preserve_markdown=True), theme.font_body, 16,
                         color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                         accent_rgb=accent, bg_rgb=bg_rgb, vertical_center=True)
    else:
        rail_zone_left = MARGIN

    items = data.items
    n_items = len(items)
    active_idx = data.active_index if data.active_index is not None else -1
    row_h = content_h / n_items
    rail_x = rail_zone_left + Inches(0.33)
    centers = [int(round(content_top + row_h * i + row_h / 2)) for i in range(n_items)]

    rail_w = Inches(0.034)
    add_rect(slide, int(rail_x - rail_w / 2), centers[0], int(rail_w), centers[-1] - centers[0],
             fill_color=rail_rgb)

    card_left = int(rail_x + Inches(0.55))
    card_w = W - card_left - MARGIN
    card_gap = Inches(0.16)
    card_h = int(min(row_h - card_gap, Inches(1.5)))
    title_size = 15 if n_items <= 4 else (14 if n_items <= 5 else (13 if n_items <= 6 else 12))
    for i, item in enumerate(items):
        cy = centers[i]
        active = (i == active_idx)
        card_top = int(cy - card_h / 2)
        add_rect(slide, int(rail_x), cy - int(Inches(0.008)), int(card_left - rail_x), Inches(0.016),
                 fill_color=rail_rgb)
        _event_card(slide, card_left, card_top, int(card_w), card_h,
                    item.fecha, item.titulo, accent_fg, bg_rgb, txt_color, theme.font_body, active,
                    title_size=title_size)
        _draw_numbered_node(slide, rail_x, cy, i + 1, accent_fg, bg_rgb, theme.font_heading, active)

    _add_notes(slide, data.notes)


def build_section_divider(prs, theme: Theme, data: SectionDividerSlide, image_registry: dict, variant: int = 0):
    """Section divider: a clean two-tone gradient whose hue varies per impact slide,
    centered title and subtitle. No decorative shapes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    c1, c2, angle, txt = _impact_gradient(theme, variant)
    _apply_gradient_background(slide, c1, c2, angle)
    W, H = prs.slide_width, prs.slide_height
    inner_x = MARGIN + Inches(0.5)
    inner_w = W - inner_x - MARGIN - Inches(0.5)
    KICK_H = Inches(0.085)
    TITLE_H = Inches(1.3)
    SUB_H = Inches(0.65) if data.subtitle else Inches(0)
    GAP_KT = Inches(0.32)
    GAP = Inches(0.28) if data.subtitle else Inches(0)
    block_h = KICK_H + GAP_KT + TITLE_H + GAP + SUB_H
    block_top = int((H - block_h) / 2)
    add_rect(slide, inner_x, block_top, Inches(0.95), KICK_H, fill_color=txt)
    add_text_box(slide, inner_x, block_top + KICK_H + GAP_KT, inner_w, TITLE_H,
                 data.title, theme.font_heading, 42,
                 bold=True, color=txt, align=PP_ALIGN.LEFT, word_wrap=True)
    if data.subtitle:
        add_text_box(slide, inner_x, block_top + KICK_H + GAP_KT + TITLE_H + GAP, inner_w, SUB_H,
                     data.subtitle, theme.font_body, 22,
                     color=txt, align=PP_ALIGN.LEFT)
    _add_notes(slide, data.notes)


def build_stat_highlight(prs, theme: Theme, data: StatHighlightSlide, image_registry: dict, variant: int = 0):
    """Spotlight a single key figure with a restrained, executive look: the number IS the hero,
    set large in the theme accent color on the clean light background, with a short accent rule,
    a bold label and an optional one-line context. No heavy colored block — this reads as an
    elegant financial/board highlight, cohesive with the rest of the light editorial deck, and
    never looks like a full-bleed section divider."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    W, H = prs.slide_width, prs.slide_height
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    accent_fg = _accent_on(accent, bg_rgb)
    set_slide_background(slide, bg_rgb)
    secondary = _blend_color(txt_color, RGBColor(128, 128, 128), 0.35)

    VALUE_H = Inches(2.1)
    RULE_W, RULE_H = Inches(1.3), Inches(0.055)
    LABEL_H = Inches(0.62)
    SUPPORT_H = Inches(0.5) if data.supporting_text else Inches(0)
    GAP_VR = Inches(0.20)
    GAP_RL = Inches(0.32)
    GAP_LS = Inches(0.16) if data.supporting_text else Inches(0)
    block_h = VALUE_H + GAP_VR + RULE_H + GAP_RL + LABEL_H + (GAP_LS + SUPPORT_H)
    block_top = int((H - block_h) / 2)

    value_size = 200 if len(data.value) <= 4 else (150 if len(data.value) <= 8 else 110)
    add_text_box(slide, MARGIN, block_top, W - MARGIN * 2, VALUE_H,
                 data.value, theme.font_heading, value_size,
                 bold=True, color=accent_fg, align=PP_ALIGN.CENTER, word_wrap=True,
                 vertical_center=True, autofit=True)

    y = block_top + VALUE_H + GAP_VR
    add_rect(slide, int((W - RULE_W) / 2), y, RULE_W, RULE_H, fill_color=accent_fg)

    y += RULE_H + GAP_RL
    add_text_box(slide, MARGIN, y, W - MARGIN * 2, LABEL_H,
                 data.label, theme.font_body, 26,
                 bold=True, color=txt_color, align=PP_ALIGN.CENTER, word_wrap=True)
    if data.supporting_text:
        y += LABEL_H + GAP_LS
        add_text_box(slide, MARGIN, y, W - MARGIN * 2, SUPPORT_H,
                     sanitize_slide_text(data.supporting_text), theme.font_body, 15,
                     color=secondary, align=PP_ALIGN.CENTER, word_wrap=True)
    _add_notes(slide, data.notes)


def build_content_text(prs, theme: Theme, data: ContentTextSlide, image_registry: dict, variant: int = 0):
    """Build a full-width body-text slide with Markdown rendering and auto-shrink."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, content_h,
                 sanitize_slide_text(data.text, preserve_markdown=True), theme.font_body, 19,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 accent_rgb=accent, bg_rgb=bg_rgb, vertical_center=True, autofit=True)
    _add_notes(slide, data.notes)


def build_content_latex(prs, theme: Theme, data: ContentLatexSlide, image_registry: dict, variant: int = 0):
    """Build a slide that renders LaTeX math expressions as images and inlines Unicode fallbacks."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_slide_background(theme, data.style_override)
    accent = hex_to_rgb(theme.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    header_bar = _resolve_header_bar(data.style_override, default=True)
    content_top = _add_accent_title_bar(slide, prs, data.title, theme.font_heading, accent, txt_color, header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    if data.layout == 'split' and data.image_id:
        gutter = Inches(0.4)
        col_w = int((W - MARGIN * 2 - gutter) / 2)
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN, content_top, col_w, content_h, valign="center")
        img_source = _resolve_image(image_registry, data.image_id)
        place_image_centered(slide, img_source, MARGIN + col_w + gutter, content_top, col_w, content_h, valign="center")
    elif data.layout == 'split' and data.text:
        gutter = Inches(0.4)
        col_w = int((W - MARGIN * 2 - gutter) / 2)
        add_text_box(slide, MARGIN, content_top, col_w, content_h,
                     sanitize_slide_text(data.text, preserve_markdown=True), theme.font_body, 16,
                     color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                     vertical_center=True, autofit=True)
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN + col_w + gutter, content_top, col_w, content_h, valign="center")
    else:
        if data.text:
            text_h = Inches(0.65)
            add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, text_h,
                         sanitize_slide_text(data.text, preserve_markdown=True), theme.font_body, 14,
                         color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True)
            content_top += text_h + Inches(0.15)
            content_h = H - content_top - MARGIN
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN, content_top, W - MARGIN * 2, content_h, valign="center")
    _add_notes(slide, data.notes)


BUILDERS = {
    "cover":            build_cover,
    "content_image":    build_content_image,
    "content_mixed":    build_content_mixed,
    "content_latex":    build_content_latex,
    "content_text":     build_content_text,
    "timeline":         build_timeline,
    "two_column":       build_two_column,
    "section_divider":  build_section_divider,
    "stat_highlight":   build_stat_highlight,
}

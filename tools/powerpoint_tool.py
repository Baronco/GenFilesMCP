import os
from io import BytesIO
from typing import Annotated, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, model_validator
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from PIL import Image as PILImage
from utils.download_file import download_file
from utils.upload_file import upload_file
from utils.knowledge import create_knowledge
from utils.get_user_id import get_user_id
from utils.authorization import _get_bearer_token
from json import dumps
from utils.logger import get_logger

logger = get_logger(__name__)

# Accepts theme tokens or an explicit hex color (#RRGGBB)
BackgroundField = Union[
    Literal["accent_color", "background_color"],
    Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")],
]

def generate_powerpoint(python_script, file_name, images_list, request, URL, ENABLE_CREATE_KNOWLEDGE, knowledge_name): 
    """
    Generate a PowerPoint file using an AI-generated Python script.

    Returns:
        dict: Contains 'file_path_download' with a markdown hyperlink for downloading the generated PowerPoint file.
    """
    try:
        images = [] # to save bytesIO images

        if len(images_list) > 0:
            logger.info(f"Received {len(images_list)} images for PPTX generation.")

        # download images
        for idx, image in enumerate(images_list):
            image_file = download_file(URL, _get_bearer_token(request), image)
            if isinstance(image_file, dict) and "error" in image_file:
                return {"error": {"message": f"Error downloading image with ID {image}: {image_file['error']['message']}"}}
            images.append(image_file)
        
        # Prepare the execution context with images
        buffer = BytesIO()
        buffer.name = f'{file_name}.pptx'
        context = {"pptx_buffer": buffer, "images": images}
        try:
            exec(python_script, context)
        except Exception as exec_e:
            return {"error": {"message": f"Error executing script: {str(exec_e)}"}}

        buffer.seek(0)

        try:
            bearer_token = _get_bearer_token(request)
            logger.info("=> Received authorization header!")
        except:
            logger.error("=> Error retrieving authorization header")

        # resolve user_id from token
        user_id = get_user_id(URL, bearer_token)
        if not user_id:
            logger.error("=> Error obtaining user id from token")
            return dumps({"error": {"message": "Error obtaining user id from token"}}, indent=4, ensure_ascii=False)

        response, request_data = upload_file(
            url=URL, 
            token=bearer_token, 
            file_data=buffer,
            filename=file_name,
            file_type="pptx"
        )

        if "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE:
            create_knowledge_status = create_knowledge(
                url=URL,
                token=bearer_token,
                file_id=request_data['id'],
                user_id=user_id,
                knowledge_name=knowledge_name
            )
            if create_knowledge_status:
                logger.info("=> Knowledge base updated successfully.")
            else:
                logger.error("=> Error creating or updating knowledge base")
        elif "error" in response:
            logger.error("=> Error uploading the file.")
        else:
            logger.info("=> Skipping knowledge creation because ENABLE_CREATE_KNOWLEDGE is false")

        return response 
    
    except Exception as e:
        logger.error("=> An unknown error occurred during .PPTX document generation.")
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            }, 
            indent=4, 
            ensure_ascii=False
        )


# ─────────────────────────── PPTX YAML helpers ────────────────────────────

class GlobalConfig(BaseModel):
    accent_color: str = Field(..., pattern=r"^#?[0-9A-Fa-f]{6}$")
    background_color: str = Field(..., pattern=r"^#?[0-9A-Fa-f]{6}$")
    font_heading: str = Field(..., min_length=1)
    font_body: str = Field(..., min_length=1)


class CoverSlide(BaseModel):
    type: Literal["cover"] = "cover"
    title: str
    subtitle: Optional[str] = ""
    date: Optional[str] = ""
    notes: Optional[str] = None


class ContentImageSlide(BaseModel):
    type: Literal["content_image"] = "content_image"
    header_bar: bool = True
    title: str
    text: str
    image_id: str
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


class TwoColumnSide(BaseModel):
    title: str
    text: str


class TwoColumnSlide(BaseModel):
    type: Literal["two_column"] = "two_column"
    title: str
    left: TwoColumnSide
    right: TwoColumnSide
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


class SectionDividerSlide(BaseModel):
    type: Literal["section_divider"] = "section_divider"
    title: str
    subtitle: Optional[str] = ""
    notes: Optional[str] = None


class ContentTextSlide(BaseModel):
    type: Literal["content_text"] = "content_text"
    header_bar: bool = True
    title: str
    text: str
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


class ChartData(BaseModel):
    type: Literal["bar", "line", "pie", "scatter", "histogram", "boxplot"]
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    values: Optional[List[float]] = None
    x: Optional[List[float]] = None
    y: Optional[List[float]] = None
    bins: Optional[int] = None          # histogram: number of bins (default 10)
    series: Optional[List[List[float]]] = None  # boxplot: one list of values per box

    @model_validator(mode="after")
    def validate_chart(self):
        if self.type in ("bar", "line", "pie"):
            if not self.categories or not self.values:
                raise ValueError(f"{self.type} charts require categories and values.")
            if len(self.categories) != len(self.values):
                raise ValueError("categories and values must have the same length.")
        elif self.type == "scatter":
            if not self.x or not self.y:
                raise ValueError("Scatter charts require x and y lists.")
            if len(self.x) != len(self.y):
                raise ValueError("Scatter x and y lists must have the same length.")
        elif self.type == "histogram":
            if not self.values:
                raise ValueError("Histogram requires values.")
        elif self.type == "boxplot":
            if not self.series:
                raise ValueError("Boxplot requires series (list of value lists).")
        return self


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]


class ContentMixedSlide(BaseModel):
    type: Literal["content_mixed"] = "content_mixed"
    header_bar: bool = True
    title: str
    text: Optional[str] = None
    image_id: Optional[str] = None
    chart: Optional[ChartData] = None
    table: Optional[TableData] = None
    background: BackgroundField = "background_color"
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_contents(self):
        contents = [bool(self.image_id), bool(self.chart), bool(self.table)]
        if sum(contents) != 1:
            raise ValueError("content_mixed requires exactly one of: image_id, chart, table.")
        return self


class ContentLatexSlide(BaseModel):
    type: Literal["content_latex"] = "content_latex"
    layout: Literal["full", "split"] = "split"
    header_bar: bool = True
    title: str
    text: Optional[str] = None
    latex_lines: List[str] = Field(
        ...,
        description=(
            "Ordered list of mathtext strings to render as a stacked image. "
            "Wrap equations in $...$, e.g. '$E = mc^2$'. "
            "Use '$\\bullet\\;$' prefix for bullet-style items, "
            "e.g. '$\\bullet\\;$ Step 1: $F = ma$'."
        ),
    )
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


Slide = Annotated[
    CoverSlide | ContentImageSlide | ContentMixedSlide | ContentLatexSlide | ContentTextSlide | TwoColumnSlide | SectionDividerSlide,
    Field(discriminator="type"),
]


class PPTXSchema(BaseModel):
    global_: GlobalConfig = Field(..., alias="global")
    slides: List[Slide]
    model_config = {"populate_by_name": True}


def hex_to_rgb(value: str) -> RGBColor:
    v = value.lstrip("#")
    return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def _resolve_background(config: "GlobalConfig", background: str):
    """Resolve background token or hex to (bg_rgb, txt_color).
    Text color is chosen automatically for contrast via relative luminance."""
    if background == "accent_color":
        bg_hex = config.accent_color
    elif background == "background_color":
        bg_hex = config.background_color
    else:
        bg_hex = background
    bg_rgb = hex_to_rgb(bg_hex)
    r, g, b = int(bg_rgb[0]), int(bg_rgb[1]), int(bg_rgb[2])
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    txt_color = RGBColor(255, 255, 255) if luminance < 0.5 else RGBColor(30, 30, 30)
    return bg_rgb, txt_color


import re as _re

# Map common LaTeX commands to Unicode equivalents used in sanitize_slide_text
_LATEX_CMD_TO_UNICODE = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
    r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
    r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
    r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Upsilon': 'Υ',
    r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
    r'\nabla': '∇', r'\partial': '∂', r'\infty': '∞',
    r'\cdot': '·', r'\times': '×', r'\sqrt': '√',
    r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\approx': '≈',
    r'\in': '∈', r'\notin': '∉', r'\subset': '⊂',
    r'\sum': 'Σ', r'\prod': 'Π', r'\int': '∫',
    r'\rightarrow': '→', r'\leftarrow': '←',
    r'\Rightarrow': '⇒', r'\Leftarrow': '⇐',
    r'\leftrightarrow': '↔', r'\hat': '', r'\vec': '', r'\bar': '',
    r'\tilde': '', r'\frac': '',
}

def sanitize_slide_text(text: str) -> str:
    """Strip markdown formatting and inline LaTeX from plain slide text."""
    if not text:
        return text
    # Literal \n sequences — convert before $ processing so \nabla isn't split
    text = text.replace('\\n', '\n')
    # $$...$$ block equations — strip delimiters, keep inner content
    text = _re.sub(r'\$\$(.+?)\$\$', lambda m: m.group(1).strip(), text, flags=_re.DOTALL)
    # $...$ inline equations — strip delimiters, keep inner content
    text = _re.sub(r'\$(.+?)\$', lambda m: m.group(1).strip(), text)
    # Bold+italic ***...*** or ______
    text = _re.sub(r'[*_]{3}(.+?)[*_]{3}', r'\1', text)
    # Bold **...** or __...__
    text = _re.sub(r'[*_]{2}(.+?)[*_]{2}', r'\1', text)
    # Italic *...* or _..._
    text = _re.sub(r'[*_](.+?)[*_]', r'\1', text)
    # Inline code `...`
    text = _re.sub(r'`(.+?)`', r'\1', text)
    # ATX headings: leading #+
    text = _re.sub(r'^#{1,6}\s+', '', text, flags=_re.MULTILINE)
    # Replace known LaTeX commands with Unicode equivalents
    for cmd, uni in _LATEX_CMD_TO_UNICODE.items():
        text = text.replace(cmd, uni)
    # \cmd{arg} → arg  (e.g. \hat{y} → y)
    text = _re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    # Remaining bare \commands → strip
    text = _re.sub(r'\\[a-zA-Z]+', '', text)
    return text


_UNSUPPORTED_MATHTEXT = (
    r'\bigg', r'\Bigg', r'\big', r'\Big',
    r'\left', r'\right',
    r'\mkern', r'\mspace', r'\hspace', r'\vspace',
    r'\text', r'\mathrm', r'\mathit', r'\mathbf',
)

def _sanitize_latex_line(line: str) -> str:
    r"""Normalize a mathtext line for matplotlib rendering.

    - Converts $$...$$ delimiters to $...$ (matplotlib uses single-dollar mathtext)
    - Collapses over-escaped backslashes (\\\\cmd -> \\cmd -> \cmd in mathtext)
    - Removes sizing/spacing commands not supported by matplotlib mathtext
    - Ensures the line has $...$ delimiters if it looks like math
    """
    if not line:
        return line
    # Convert $$...$$ to $...$ (model often outputs display-math delimiters)
    line = line.replace('$$', '$')
    # Collapse double-backslash to single (over-escaped by model)
    while '\\\\' in line:
        line = line.replace('\\\\', '\\')
    # Remove unsupported commands, keeping just their argument if parenthesised
    for cmd in _UNSUPPORTED_MATHTEXT:
        line = line.replace(cmd, '')
    return line


def set_slide_background(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _parse_inline_markdown(text: str):
    """Parse inline markdown and return list of (segment_text, bold, italic) tuples.
    Supports: **bold**, *italic*, ***bold+italic***, `code` (treated as bold mono).
    """
    import re
    pattern = re.compile(
        r'(\*\*\*(?P<bolditalic>.+?)\*\*\*)'
        r'|(\*\*(?P<bold>.+?)\*\*)'
        r'|(\*(?P<italic>.+?)\*)'
        r'|(__(?P<bold2>.+?)__)'
        r'|(_(?P<italic2>.+?)_)'
        r'|(`(?P<code>.+?)`)',
        re.DOTALL,
    )
    segments = []
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            segments.append((text[last:m.start()], False, False))
        if m.group('bolditalic'):
            segments.append((m.group('bolditalic'), True, True))
        elif m.group('bold') or m.group('bold2'):
            t = m.group('bold') or m.group('bold2')
            segments.append((t, True, False))
        elif m.group('italic') or m.group('italic2'):
            t = m.group('italic') or m.group('italic2')
            segments.append((t, False, True))
        elif m.group('code'):
            segments.append((m.group('code'), True, False))
        last = m.end()
    if last < len(text):
        segments.append((text[last:], False, False))
    return segments if segments else [(text, False, False)]


def _add_run_to_paragraph(p, text, font_name, font_size, bold, italic, color):
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return run


def _parse_md_table(table_lines: list) -> Optional['TableData']:
    """Parse a list of markdown table lines (header, separator, rows) into TableData."""
    if len(table_lines) < 2:
        return None

    def split_row(line):
        return [c.strip() for c in line.strip().strip('|').split('|')]

    headers = split_row(table_lines[0])
    # table_lines[1] is the separator — skip it
    rows = [split_row(line) for line in table_lines[2:] if line.strip() and '|' in line]
    n = len(headers)
    normalized = []
    for row in rows:
        if len(row) < n:
            row = row + [''] * (n - len(row))
        elif len(row) > n:
            row = row[:n]
        normalized.append(row)
    if not headers:
        return None
    return TableData(headers=headers, rows=normalized)


def _split_text_and_tables(text: str):
    """Split markdown text into segments: ('text', str) or ('table', TableData).
    Detects standard pipe-table syntax: header row | separator row | data rows.
    """
    lines = text.splitlines()
    segments = []
    current_lines: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Pipe table: current line has | and next line is all dashes/colons/pipes
        if ('|' in line and line.strip().startswith('|')
                and i + 1 < len(lines)
                and _re.match(r'^\s*\|[\s\-:|]+\|\s*$', lines[i + 1])):
            if current_lines:
                combined = '\n'.join(current_lines).strip()
                if combined:
                    segments.append(('text', combined))
                current_lines = []
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            td = _parse_md_table(table_lines)
            if td:
                segments.append(('table', td))
        else:
            current_lines.append(line)
            i += 1
    if current_lines:
        combined = '\n'.join(current_lines).strip()
        if combined:
            segments.append(('text', combined))
    return segments if segments else [('text', text)]


def _fill_textbox_markdown(tf, text, font_name, font_size, bold, italic, color, align):
    """Fill an existing text frame with markdown-formatted lines."""
    lines = text.replace('\\n', '\n').splitlines()
    first_paragraph = True
    for line in lines:
        stripped = line.rstrip()
        is_bullet = bool(_re.match(r'^(\s*[-*•]\s+|\s*\d+\.\s+)', stripped))
        if is_bullet:
            m = _re.match(r'^(\s*)([-*•]|\d+\.)\s+', stripped)
            if m:
                stripped = stripped[m.end():]
                prefix = '• '
            else:
                prefix = ''
        else:
            prefix = ''
        if first_paragraph:
            p = tf.paragraphs[0]
            first_paragraph = False
        else:
            p = tf.add_paragraph()
        p.alignment = align if not is_bullet else PP_ALIGN.LEFT
        if is_bullet:
            p.level = 1
        for seg_text, seg_bold, seg_italic in _parse_inline_markdown(prefix + stripped):
            _add_run_to_paragraph(p, seg_text, font_name, font_size,
                                  bold or seg_bold, italic or seg_italic, color)


def add_text_box(
    slide,
    left, top, width, height,
    text,
    font_name, font_size,
    bold=False, italic=False,
    color=RGBColor(0, 0, 0),
    align=PP_ALIGN.CENTER,
    word_wrap=True,
    markdown=False,
    accent_rgb: RGBColor = None,
    bg_rgb: RGBColor = None,
):
    """Add a text box. markdown=True parses bold/italic/bullets.
    Embedded markdown pipe tables are automatically detected and rendered as real PPTX tables.
    """
    if not markdown or not text:
        shape = slide.shapes.add_textbox(left, top, width, height)
        shape.text_frame.word_wrap = word_wrap
        shape.text_frame.clear()
        p = shape.text_frame.paragraphs[0]
        p.alignment = align
        _add_run_to_paragraph(p, text or '', font_name, font_size, bold, italic, color)
        return shape

    # Detect embedded markdown tables
    segments = _split_text_and_tables(text.replace('\\n', '\n'))
    has_table = any(seg_type == 'table' for seg_type, _ in segments)

    if not has_table:
        shape = slide.shapes.add_textbox(left, top, width, height)
        shape.text_frame.word_wrap = word_wrap
        shape.text_frame.clear()
        _fill_textbox_markdown(shape.text_frame, text, font_name, font_size,
                               bold, italic, color, align)
        return shape

    # Mixed text + table: stack segments vertically within the given bounds
    gap = Inches(0.12)
    n_text = sum(1 for t, _ in segments if t == 'text')
    tbl_heights = []
    for seg_type, seg_content in segments:
        if seg_type == 'table':
            ideal = (len(seg_content.rows) + 1) * Inches(0.40)
            tbl_heights.append(min(ideal, Inches(2.5)))
    total_tbl_h = sum(tbl_heights)
    total_gaps = (len(segments) - 1) * gap
    remaining_text_h = max(height - total_tbl_h - total_gaps, Inches(0.4) * max(n_text, 1))
    text_h_each = int(remaining_text_h // max(n_text, 1))

    y = top
    tbl_idx = 0
    last_shape = None
    for seg_type, seg_content in segments:
        remaining = top + height - y
        if remaining < Inches(0.2):
            break
        if seg_type == 'text':
            seg_h = min(text_h_each, remaining)
            shape = slide.shapes.add_textbox(left, y, width, seg_h)
            shape.text_frame.word_wrap = word_wrap
            shape.text_frame.clear()
            _fill_textbox_markdown(shape.text_frame, seg_content, font_name, font_size,
                                   bold, italic, color, align)
            last_shape = shape
            y += seg_h + gap
        else:
            seg_h = min(tbl_heights[tbl_idx], remaining)
            tbl_idx += 1
            add_table(slide, seg_content, left, y, width, seg_h, font_name,
                      accent_rgb=accent_rgb, bg_rgb=bg_rgb, txt_color=color)
            y += seg_h + gap
    return last_shape


def add_header_bar(slide, prs, title, font_name, accent_rgb, bar_height=Inches(0.8)):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, bar_height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent_rgb
    bar.line.fill.background()
    tf = bar.text_frame
    tf.word_wrap = False
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title
    run.font.name = font_name
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.color.rgb = RGBColor(255, 255, 255)
    return bar_height


def place_image_centered(slide, img_source, left, top, max_width, max_height):
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

    offset_x = int((max_width - final_w) / 2)
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


def add_chart(slide, chart_def: ChartData, left, top, width, height,
              accent_rgb: RGBColor = None, bg_rgb: RGBColor = None,
              txt_color: RGBColor = None):
    """Render a styled chart as a matplotlib image and embed it in the slide."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import colorsys

    _accent = accent_rgb or RGBColor(0x0D, 0x94, 0x88)
    _txt = txt_color or RGBColor(30, 30, 30)
    acc = (_accent[0] / 255, _accent[1] / 255, _accent[2] / 255)
    txt = (_txt[0] / 255, _txt[1] / 255, _txt[2] / 255)
    txt_a = txt + (0.45,)  # semi-transparent for spines/grid

    def _palette(n):
        h, s, v = colorsys.rgb_to_hsv(*acc)
        out = []
        for i in range(n):
            h2 = (h + i * 0.13) % 1.0
            s2 = max(0.25, s - i * 0.05)
            v2 = min(1.0, v + 0.08 * (i % 3 == 2))
            out.append(colorsys.hsv_to_rgb(h2, s2, v2))
        return out

    fig_w = max(4.5, width / 914400)
    fig_h = max(3.0, height / 914400)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(txt_a)
    ax.spines['bottom'].set_color(txt_a)
    ax.tick_params(axis='both', colors=txt, labelsize=8, length=3)

    ct = chart_def.type
    if ct == 'bar':
        xs = list(range(len(chart_def.categories)))
        ax.bar(xs, chart_def.values, color=acc, width=0.55, zorder=3,
               edgecolor='white', linewidth=0.5)
        ax.set_xticks(xs)
        ax.set_xticklabels(chart_def.categories, color=txt, fontsize=8)
        ax.grid(axis='y', color=txt, alpha=0.12, linewidth=0.7, zorder=0)

    elif ct == 'line':
        xs = list(range(len(chart_def.categories)))
        ax.plot(xs, chart_def.values, color=acc, linewidth=2.2,
                marker='o', markersize=5, markerfacecolor='white',
                markeredgewidth=2, zorder=3)
        ax.fill_between(xs, chart_def.values, alpha=0.12, color=acc)
        ax.set_xticks(xs)
        ax.set_xticklabels(chart_def.categories, color=txt, fontsize=8)
        ax.grid(axis='y', color=txt, alpha=0.12, linewidth=0.7, zorder=0)

    elif ct == 'pie':
        colors = _palette(len(chart_def.values))
        wedges, texts, autotexts = ax.pie(
            chart_def.values, labels=chart_def.categories, colors=colors,
            autopct='%1.0f%%', startangle=140,
            wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
        )
        for t in texts:
            t.set_color(txt)
            t.set_fontsize(8)
        for at in autotexts:
            at.set_color('white')
            at.set_fontsize(8)

    elif ct == 'scatter':
        ax.scatter(chart_def.x, chart_def.y, color=acc, s=42, alpha=0.85,
                   edgecolors='white', linewidths=0.5, zorder=3)
        ax.grid(color=txt, alpha=0.10, linewidth=0.7, zorder=0)

    elif ct == 'histogram':
        bins = chart_def.bins or 10
        ax.hist(chart_def.values, bins=bins, color=acc,
                edgecolor='white', linewidth=0.6, zorder=3)
        ax.grid(axis='y', color=txt, alpha=0.12, linewidth=0.7, zorder=0)

    elif ct == 'boxplot':
        series = chart_def.series or []
        labels = chart_def.categories or [str(i + 1) for i in range(len(series))]
        bp = ax.boxplot(
            series, patch_artist=True, labels=labels,
            medianprops=dict(color='white', linewidth=2),
            whiskerprops=dict(color=acc, linewidth=1.4),
            capprops=dict(color=acc, linewidth=1.4),
            flierprops=dict(marker='o', markerfacecolor=acc, markersize=4,
                            markeredgecolor='white', markeredgewidth=0.5),
            boxprops=dict(linewidth=0),
        )
        for patch in bp['boxes']:
            patch.set_facecolor(acc)
            patch.set_alpha(0.78)
        ax.grid(axis='y', color=txt, alpha=0.12, linewidth=0.7, zorder=0)

    if chart_def.title and ct != 'pie':
        ax.set_title(chart_def.title, color=txt, fontsize=10, fontweight='bold', pad=6)

    plt.tight_layout(pad=0.5)
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, transparent=True, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    place_image_centered(slide, buf, left, top, width, height)


def add_table(slide, table_def: TableData, left, top, width, height, font_name,
              font_size: int = 11, accent_rgb: RGBColor = None,
              bg_rgb: RGBColor = None, txt_color: RGBColor = None):
    """Add a styled table: accent-colored header row, alternating row backgrounds."""
    _accent = accent_rgb or RGBColor(0x0D, 0x94, 0x88)
    _bg = bg_rgb or RGBColor(0xF0, 0xFD, 0xFA)
    _txt = txt_color or RGBColor(30, 30, 30)
    # Slightly tinted alternate row color
    alt_rgb = RGBColor(
        min(255, int(_bg[0] * 0.93 + _accent[0] * 0.07)),
        min(255, int(_bg[1] * 0.93 + _accent[1] * 0.07)),
        min(255, int(_bg[2] * 0.93 + _accent[2] * 0.07)),
    )
    rows = len(table_def.rows) + 1
    cols = len(table_def.headers)
    row_height = Inches(0.40)
    actual_height = min(rows * row_height, height)
    tbl_shape = slide.shapes.add_table(rows, cols, left, top, width, actual_height)
    tbl = tbl_shape.table
    # Header row
    for ci, header in enumerate(table_def.headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _accent
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.text = str(header)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
    # Data rows
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
    sep = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, top, x, bottom)
    sep.line.width = Pt(1.5)
    sep.line.color.rgb = accent_rgb


MARGIN = Inches(0.6)
BAR_H = Inches(0.8)


def _add_notes(slide, text: Optional[str]) -> None:
    """Write presenter notes to the slide's notes pane."""
    if not text:
        return
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = text


def _render_latex_to_image(
    latex_lines: list,
    bg_rgb: RGBColor,
    txt_rgb: RGBColor,
    dpi: int = 150,
) -> BytesIO:
    """Render a list of mathtext strings to a transparent PNG image in memory."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fg = (txt_rgb[0] / 255, txt_rgb[1] / 255, txt_rgb[2] / 255)
    n = max(len(latex_lines), 1)
    fig_h = max(1.5, n * 0.85)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    for i, raw_line in enumerate(latex_lines):
        line = _sanitize_latex_line(raw_line)
        y = 1.0 - (i + 0.5) / n
        try:
            ax.text(
                0.02, y, line,
                transform=ax.transAxes,
                fontsize=18,
                color=fg,
                verticalalignment='center',
                horizontalalignment='left',
            )
        except Exception:
            plain = _re.sub(r'\$', '', line)
            plain = _re.sub(r'\\[a-zA-Z]+', '', plain)
            plain = plain.strip()
            ax.text(
                0.02, y, plain,
                transform=ax.transAxes,
                fontsize=18,
                color=fg,
                verticalalignment='center',
                horizontalalignment='left',
                parse_math=False,
            )
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


def build_cover(prs, config: GlobalConfig, data: CoverSlide, image_registry: dict):
    """Clean cover: full accent background, all content vertically and horizontally centered."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, accent)
    W, H = prs.slide_width, prs.slide_height
    white = RGBColor(255, 255, 255)
    inner_x = MARGIN + Inches(0.4)
    inner_w = W - (MARGIN + Inches(0.4)) * 2

    # Compute total block height for vertical centering
    TITLE_H = Inches(1.6)
    SUB_H = Inches(0.55) if data.subtitle else Inches(0)
    DATE_H = Inches(0.35) if data.date else Inches(0)
    GAP_TS = Inches(0.28) if data.subtitle else Inches(0)
    GAP_SD = Inches(0.18) if data.date else Inches(0)
    block_h = TITLE_H + GAP_TS + SUB_H + GAP_SD + DATE_H
    block_top = int((H - block_h) / 2)

    add_text_box(slide, inner_x, block_top, inner_w, TITLE_H,
                 data.title, config.font_heading, 46,
                 bold=True, color=white, align=PP_ALIGN.CENTER)
    y = block_top + TITLE_H + GAP_TS
    if data.subtitle:
        add_text_box(slide, inner_x, y, inner_w, SUB_H,
                     data.subtitle, config.font_body, 22,
                     italic=True, color=RGBColor(240, 245, 250), align=PP_ALIGN.CENTER)
        y += SUB_H + GAP_SD
    if data.date:
        add_text_box(slide, inner_x, y, inner_w, DATE_H,
                     data.date, config.font_body, 14,
                     color=RGBColor(220, 235, 248), align=PP_ALIGN.CENTER)
    _add_notes(slide, data.notes)


def _add_accent_title_bar(slide, prs, title, font_name, accent_rgb, txt_color, header_bar, bg_rgb):
    """Unified title rendering. Returns content_top (Inches position after title area).
    - header_bar=True: full-width colored bar with white text
    - header_bar=False: plain title + thin accent underline rule
    """
    W = prs.slide_width
    if header_bar:
        return add_header_bar(slide, prs, title, font_name, accent_rgb)
    else:
        title_top = Inches(0.35)
        title_h = Inches(0.65)
        add_text_box(slide, MARGIN, title_top, W - MARGIN * 2, title_h,
                     title, font_name, 26, bold=True, color=txt_color, align=PP_ALIGN.LEFT)
        # thin accent underline
        rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, title_top + title_h, W - MARGIN * 2, Inches(0.04))
        rule.fill.solid()
        rule.fill.fore_color.rgb = accent_rgb
        rule.line.fill.background()
        return title_top + title_h + Inches(0.1)


def build_content_image(prs, config: GlobalConfig, data: ContentImageSlide, image_registry: dict):
    """Left-text / Right-image layout."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, data.header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    gutter = Inches(0.4)
    text_col_w = int((W - MARGIN * 2 - gutter) * 0.42)
    img_col_w = int((W - MARGIN * 2 - gutter) * 0.58)
    add_text_box(slide, MARGIN, content_top, text_col_w, content_h,
                 sanitize_slide_text(data.text), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True)
    img_x = MARGIN + text_col_w + gutter
    img_source = _resolve_image(image_registry, data.image_id)
    place_image_centered(slide, img_source, img_x, content_top + Inches(0.1), img_col_w, content_h - Inches(0.2))
    _add_notes(slide, data.notes)


def build_two_column(prs, config: GlobalConfig, data: TwoColumnSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, False, bg_rgb)
    content_top += Inches(0.3)  # breathing room below main title
    content_h = H - content_top - MARGIN
    gutter = Inches(0.5)  # wider gap provides visual separation without a line
    col_w = int((W - MARGIN * 2 - gutter) / 2)
    _build_column(slide, MARGIN, content_top, col_w, content_h,
                  sanitize_slide_text(data.left.title), data.left.text,
                  config.font_heading, config.font_body, txt_color, accent)
    _build_column(slide, MARGIN + col_w + gutter, content_top, col_w, content_h,
                  sanitize_slide_text(data.right.title), data.right.text,
                  config.font_heading, config.font_body, txt_color, accent)
    _add_notes(slide, data.notes)


def _build_column(slide, left, top, width, height,
                  title, text, font_heading, font_body, txt_color, accent):
    """Render a single column: accent-colored header rectangle + body text."""
    title_h = Inches(0.52)
    # Accent-colored header rectangle defining the column title zone
    header_rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, title_h)
    header_rect.fill.solid()
    header_rect.fill.fore_color.rgb = accent
    header_rect.line.fill.background()
    # Title text over the colored header
    add_text_box(slide, left + Inches(0.1), top + Inches(0.05),
                 width - Inches(0.12), title_h - Inches(0.08),
                 title, font_heading, 15,
                 bold=True, color=RGBColor(255, 255, 255), align=PP_ALIGN.LEFT)
    # Body text below
    body_top = top + title_h + Inches(0.22)
    body_h = height - title_h - Inches(0.22)
    add_text_box(slide, left, body_top, width, body_h,
                 sanitize_slide_text(text), font_body, 13,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True)


def build_content_mixed(prs, config: GlobalConfig, data: ContentMixedSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, data.header_bar, bg_rgb)
    content_top += Inches(0.3)
    gutter = Inches(0.4)
    col_w = int((W - MARGIN * 2 - gutter) / 2)
    content_h = H - content_top - MARGIN
    add_text_box(slide, MARGIN, content_top, col_w, content_h,
                 sanitize_slide_text(data.text or ''), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 accent_rgb=accent, bg_rgb=bg_rgb)
    right_x = MARGIN + col_w + gutter
    if data.image_id:
        img_source = _resolve_image(image_registry, data.image_id)
        place_image_centered(slide, img_source, right_x, content_top, col_w, content_h)
    elif data.chart:
        add_chart(slide, data.chart, right_x, content_top, col_w, content_h,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color)
    elif data.table:
        add_table(slide, data.table, right_x, content_top + Inches(0.1), col_w,
                  content_h - Inches(0.1), config.font_body,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color)
    _add_notes(slide, data.notes)


def build_section_divider(prs, config: GlobalConfig, data: SectionDividerSlide, image_registry: dict):
    """Section divider: full accent background, centered title and subtitle."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, accent)
    W, H = prs.slide_width, prs.slide_height
    inner_w = W - MARGIN * 2
    white = RGBColor(255, 255, 255)
    near_white = RGBColor(240, 245, 250)
    TITLE_H = Inches(1.1)
    SUB_H = Inches(0.65) if data.subtitle else Inches(0)
    GAP = Inches(0.25) if data.subtitle else Inches(0)
    block_h = TITLE_H + GAP + SUB_H
    block_top = int((H - block_h) / 2)
    add_text_box(slide, MARGIN, block_top, inner_w, TITLE_H,
                 data.title, config.font_heading, 40,
                 bold=True, color=white, align=PP_ALIGN.CENTER)
    if data.subtitle:
        add_text_box(slide, MARGIN, block_top + TITLE_H + GAP, inner_w, SUB_H,
                     data.subtitle, config.font_body, 22,
                     italic=True, color=near_white, align=PP_ALIGN.CENTER)
    _add_notes(slide, data.notes)


def build_content_text(prs, config: GlobalConfig, data: ContentTextSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, data.header_bar, bg_rgb)
    content_top += Inches(0.3)  # breathing room below title
    content_h = H - content_top - MARGIN
    add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, content_h,
                 sanitize_slide_text(data.text), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 accent_rgb=accent, bg_rgb=bg_rgb)
    _add_notes(slide, data.notes)


def build_content_latex(prs, config: GlobalConfig, data: ContentLatexSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, data.header_bar, bg_rgb)
    content_top += Inches(0.3)
    content_h = H - content_top - MARGIN
    if data.layout == 'split' and data.text:
        # Split layout: descriptive text on the left, equations image on the right
        gutter = Inches(0.4)
        col_w = int((W - MARGIN * 2 - gutter) / 2)
        add_text_box(slide, MARGIN, content_top, col_w, content_h,
                     sanitize_slide_text(data.text), config.font_body, 15,
                     color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True)
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN + col_w + gutter, content_top, col_w, content_h)
    else:
        # Full layout: optional intro text above, then full-width equations image
        if data.text:
            text_h = Inches(0.65)
            add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, text_h,
                         sanitize_slide_text(data.text), config.font_body, 14,
                         color=txt_color, align=PP_ALIGN.LEFT)
            content_top += text_h + Inches(0.15)
            content_h = H - content_top - MARGIN
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN, content_top, W - MARGIN * 2, content_h)
    _add_notes(slide, data.notes)


BUILDERS = {
    "cover":            build_cover,
    "content_image":    build_content_image,
    "content_mixed":    build_content_mixed,
    "content_latex":    build_content_latex,
    "content_text":     build_content_text,
    "two_column":       build_two_column,
    "section_divider":  build_section_divider,
}


def create_presentation_from_yaml(
    yaml_text: str,
    output_buffer,
    image_registry: dict = None,
) -> BytesIO:
    image_registry = image_registry or {}

    # Strip YAML-illegal control characters (\x00-\x08, \x0b-\x1f except \t\n\r)
    yaml_text = _re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', yaml_text)

    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("YAML must be a mapping at the top level.")

    # Normalize: if model omitted the 'global' wrapper and put fields at top level
    if 'global' not in raw and 'accent_color' in raw:
        global_keys = {'accent_color', 'background_color', 'font_heading', 'font_body'}
        global_data = {k: raw.pop(k) for k in list(raw) if k in global_keys}
        raw = {'global': global_data, **raw}

    # Normalize: common alternate names for 'slides'
    if 'slides' not in raw:
        for alt in ('slide_list', 'slide', 'pages', 'content'):
            if alt in raw:
                raw['slides'] = raw.pop(alt)
                break

    schema = PPTXSchema.model_validate(raw)
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)

    for slide_data in schema.slides:
        builder = BUILDERS.get(slide_data.type)
        if not builder:
            raise ValueError(f"Slide type not implemented: {slide_data.type}")
        builder(prs, schema.global_, slide_data, image_registry)

    prs.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def _extract_image_ids_from_yaml(parsed_yaml) -> list[str]:
    image_ids: list[str] = []

    if isinstance(parsed_yaml, dict):
        for key, value in parsed_yaml.items():
            if key == "image_id" and isinstance(value, str):
                image_ids.append(value)
            else:
                image_ids.extend(_extract_image_ids_from_yaml(value))
    elif isinstance(parsed_yaml, list):
        for item in parsed_yaml:
            image_ids.extend(_extract_image_ids_from_yaml(item))

    return image_ids


def generate_powerpoint_structured_yaml(
    document_yaml,
    file_name,
    request,
    URL,
    ENABLE_CREATE_KNOWLEDGE,
    knowledge_name,
):
    try:
        try:
            parsed_yaml = yaml.safe_load(document_yaml)
        except yaml.YAMLError as exc:
            return {"error": {"message": f"YAML parse error: {exc}"}}

        image_ids = list(dict.fromkeys(_extract_image_ids_from_yaml(parsed_yaml)))
        images = []

        if image_ids:
            logger.info(f"Received {len(image_ids)} image references for PPTX YAML generation.")

        for image_id in image_ids:
            image_file = download_file(URL, _get_bearer_token(request), image_id)
            if isinstance(image_file, dict) and "error" in image_file:
                return {"error": {"message": f"Error downloading image with ID {image_id}: {image_file['error']['message']}"}}
            image_file.seek(0)
            images.append(image_file)

        image_registry = {image_id: image_file for image_id, image_file in zip(image_ids, images)}
        buffer = BytesIO()
        buffer.name = f"{file_name}.pptx"

        try:
            create_presentation_from_yaml(document_yaml, buffer, image_registry)
        except Exception as exec_e:
            return {"error": {"message": f"Error generating PowerPoint from YAML: {str(exec_e)}"}}

        buffer.seek(0)

        try:
            bearer_token = _get_bearer_token(request)
            if bearer_token:
                logger.info("=> Received authorization header!")
            else:
                logger.warning("=> Authorization header is missing.")
        except Exception:
            logger.exception("=> Error retrieving authorization header")
            bearer_token = None

        user_id = None
        if bearer_token:
            user_id = get_user_id(URL, bearer_token)
            if not user_id:
                logger.warning("=> Could not obtain user id from token; continuing without knowledge creation.")

        response, request_data = upload_file(
            url=URL,
            token=bearer_token,
            file_data=buffer,
            filename=file_name,
            file_type="pptx"
        )

        if "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE and user_id:
            create_knowledge_status = create_knowledge(
                url=URL,
                token=bearer_token,
                file_id=request_data['id'],
                user_id=user_id,
                knowledge_name=knowledge_name
            )
            if create_knowledge_status:
                logger.info("=> Knowledge base updated successfully.")
            else:
                logger.error("=> Error creating or updating knowledge base")
        elif "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE and not user_id:
            logger.warning("=> Skipping knowledge creation because user_id is unavailable.")
        elif "error" in response:
            logger.error("=> Error uploading the file.")
        else:
            logger.info("=> Skipping knowledge creation because ENABLE_CREATE_KNOWLEDGE is false")

        return response
    except Exception as e:
        logger.error("=> An unknown error occurred during .PPTX document generation from YAML.")
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            },
            indent=4,
            ensure_ascii=False
        )
import os
from io import BytesIO
from typing import Annotated, List, Literal, Optional, Union

import pandas as pd
import yaml
from pydantic import BaseModel, Field, model_validator
from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt
from utils.charts import chart
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

TextStyle = Literal["prose", "bullets"]

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
    text_style: TextStyle = "prose"
    image_id: str
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


class TwoColumnSide(BaseModel):
    title: str
    text: str
    text_style: TextStyle = "prose"


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
    text_style: TextStyle = "prose"
    background: BackgroundField = "background_color"
    notes: Optional[str] = None


class ChartData(BaseModel):
    type: Optional[Literal[
        "bar", "line", "pie", "scatter", "hist", "histogram", "count",
        "point", "box", "violin", "strip", "swarm", "bubble",
        "lmplot", "lmplot_facet", "joint", "joint_hex", "joint_kde",
        "logistic", "resid", "heatmap", "clustermap", "pair", "pair_kde",
        "timeseries", "timeseries_facet", "ridge", "boxen", "ecdf", "chart",
    ]] = None
    kind: Optional[str] = None
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    values: Optional[List[float]] = None
    columns: Optional[List[str]] = None
    x: Optional[Union[str, List[str]]] = None
    y: Optional[Union[str, List[str]]] = None
    size: Optional[str] = None
    z: Optional[str] = None
    col: Optional[str] = None
    col_wrap: Optional[int] = None
    hue: Optional[Union[str, List[str]]] = None
    palette: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    group: Optional[str] = None
    bins: Optional[int] = None          # histogram: number of bins (default 10)
    kernels: Optional[List[str]] = None
    bw_adjusts: Optional[List[float]] = None
    line_kws: Optional[dict] = None
    data: Optional[dict] = None
    chart_kwargs: Optional[dict] = None

    @model_validator(mode="after")
    def validate_chart(self):
        chart_kind = self.kind if self.type == "chart" else self.kind or self.type
        if not chart_kind:
            raise ValueError("chart requires a 'type' or 'kind' field.")
        if self.data is None:
            if chart_kind in ("bar", "line", "pie"):
                if not self.categories or not self.values:
                    raise ValueError(f"{chart_kind} charts require categories and values.")
                if isinstance(self.categories, list) and isinstance(self.values, list):
                    if len(self.categories) != len(self.values):
                        min_len = min(len(self.categories), len(self.values))
                        self.categories = self.categories[:min_len]
                        self.values = self.values[:min_len]
            elif chart_kind == "scatter":
                if not self.x or not self.y:
                    raise ValueError("Scatter charts require x and y lists.")
                if isinstance(self.x, list) and isinstance(self.y, list) and len(self.x) != len(self.y):
                    min_len = min(len(self.x), len(self.y))
                    self.x = self.x[:min_len]
                    self.y = self.y[:min_len]
            elif chart_kind == "histogram":
                if not self.values:
                    raise ValueError("Histogram requires values.")
        return self


class TableData(BaseModel):
    headers: List[str]
    rows: List[List[str]]


class ContentMixedSlide(BaseModel):
    type: Literal["content_mixed"] = "content_mixed"
    header_bar: bool = True
    title: str
    text: Optional[str] = None
    text_style: TextStyle = "prose"
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


class TimelineEvent(BaseModel):
    fecha: str
    titulo: str
    emoji: Optional[str] = None


class TimelineSlide(BaseModel):
    type: Literal["timeline"] = "timeline"
    title: str
    items: List[TimelineEvent]
    active_index: Optional[int] = None
    background: BackgroundField = "background_color"
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items or len(self.items) < 2:
            raise ValueError("timeline requires at least two items.")
        if self.active_index is not None and not (0 <= self.active_index < len(self.items)):
            raise ValueError("timeline.active_index must refer to a valid item index.")
        return self


class ContentLatexSlide(BaseModel):
    type: Literal["content_latex"] = "content_latex"
    layout: Literal["full", "split"] = "split"
    header_bar: bool = True
    title: str
    text: Optional[str] = None
    text_style: TextStyle = "prose"
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
    CoverSlide | ContentImageSlide | ContentMixedSlide | ContentLatexSlide | ContentTextSlide | TimelineSlide | TwoColumnSlide | SectionDividerSlide,
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

def sanitize_slide_text(text: str, preserve_markdown: bool = False) -> str:
    """Strip markdown formatting and inline LaTeX from plain slide text.
    If preserve_markdown=True, keep bold/italic/code markers so the PowerPoint
    markdown renderer can apply formatting while still normalizing headings
    and math delimiters.
    """
    if not text:
        return text
    # Literal \n sequences — convert before $ processing so \nabla isn't split
    text = text.replace('\\n', '\n')
    # $$...$$ block equations — strip delimiters, keep inner content
    text = _re.sub(r'\$\$(.+?)\$\$', lambda m: m.group(1).strip(), text, flags=_re.DOTALL)
    # $...$ inline equations — strip delimiters, keep inner content
    text = _re.sub(r'\$(.+?)\$', lambda m: m.group(1).strip(), text)
    if not preserve_markdown:
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
    r'\mathrm', r'\mathit', r'\mathbf',
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
    # Translate markdown-style bold/italic into mathtext commands
    line = _re.sub(r'\*\*(.+?)\*\*', r'\\mathbf{\1}', line)
    line = _re.sub(r'\*(.+?)\*', r'\\mathit{\1}', line)
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


def _make_paragraph_bullet_pointed(p):
    pPr = p._p.get_or_add_pPr()
    pPr.set('marL', '342900')
    pPr.set('indent', '-171450')
    buFont = OxmlElement('a:buFont')
    buFont.set('typeface', 'Arial')
    buFont.set('panose', '020B0604020202020204')
    buFont.set('pitchFamily', '34')
    buFont.set('charset', '0')
    pPr.append(buFont)
    buChar = OxmlElement('a:buChar')
    buChar.set('char', '•')
    pPr.append(buChar)


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
            if first_paragraph:
                p = tf.paragraphs[0]
                first_paragraph = False
            else:
                p = tf.add_paragraph()
            _make_paragraph_bullet_pointed(p)
            p.alignment = PP_ALIGN.LEFT
            p.level = 0
        else:
            if first_paragraph:
                p = tf.paragraphs[0]
                first_paragraph = False
            else:
                p = tf.add_paragraph()
            p.alignment = align
        for seg_text, seg_bold, seg_italic in _parse_inline_markdown(stripped):
            _add_run_to_paragraph(p, seg_text, font_name, font_size,
                                  bold or seg_bold, italic or seg_italic, color)


def _force_bullet_text(text: str) -> str:
    lines = text.replace('\\n', '\n').splitlines()
    normalized = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            normalized.append('')
            continue
        if _re.match(r'^(\s*[-*•]|\s*\d+\.)\s+', stripped):
            normalized.append(stripped)
        else:
            normalized.append(f'- {stripped}')
    return '\n'.join(normalized)


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
    text_style: Literal["prose", "bullets"] = "prose",
    accent_rgb: RGBColor = None,
    bg_rgb: RGBColor = None,
):
    """Add a text box. markdown=True parses bold/italic/bullets.
    text_style='bullets' forces every non-empty line into a bullet item.
    Embedded markdown pipe tables are automatically detected and rendered as real PPTX tables.
    """
    if text and text_style == "bullets":
        text = _force_bullet_text(text)

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

    text_box = slide.shapes.add_textbox(0, 0, prs.slide_width, bar_height)
    text_box.fill.background()
    text_box.line.fill.background()
    tf = text_box.text_frame
    tf.margin_top = Inches(0.15)
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
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


def place_image_centered(slide, img_source, left, top, max_width, max_height,
                          valign: str = "center", halign: str = "center"):
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


def add_rect(slide, x, y, w, h, fill_color, line_color=None, line_w_pt=0):
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
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
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


def add_line_shape(slide, x1, y1, x2, y2, color, width_pt=1.5, dash=False):
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(width_pt)
    if dash:
        connector.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return connector


def _render_chart_image(chart_def: ChartData, width, height):
    kind = chart_def.kind or chart_def.type
    if not kind:
        raise ValueError("chart requires a 'type' or 'kind' field.")
    kind = kind if kind != "histogram" else "hist"

    kwargs = {
        "save_path": None,
    }
    hue_col_name = None
    if chart_def.hue is not None and not isinstance(chart_def.hue, list):
        kwargs["hue"] = chart_def.hue
    if chart_def.palette is not None:
        kwargs["palette"] = chart_def.palette
    if chart_def.xlabel is not None:
        kwargs["xlabel"] = chart_def.xlabel
    if chart_def.ylabel is not None:
        kwargs["ylabel"] = chart_def.ylabel
    if chart_def.group is not None:
        kwargs["group"] = chart_def.group
    if chart_def.col is not None:
        kwargs["col"] = chart_def.col
    if chart_def.col_wrap is not None:
        kwargs["col_wrap"] = chart_def.col_wrap
    if chart_def.title is not None:
        kwargs["title"] = chart_def.title
    if chart_def.bins is not None:
        kwargs["bins"] = chart_def.bins
    if chart_def.kernels is not None:
        kwargs["kernels"] = chart_def.kernels
    if chart_def.bw_adjusts is not None:
        kwargs["bw_adjusts"] = chart_def.bw_adjusts
    if chart_def.line_kws is not None:
        kwargs["line_kws"] = chart_def.line_kws
    if chart_def.chart_kwargs:
        kwargs.update(chart_def.chart_kwargs)

    if chart_def.data is not None:
        if not isinstance(chart_def.data, dict):
            raise ValueError("chart.data must be a dict of series, e.g. {x: [1,2,3], y: [4,5,6]}")
        data_dict = dict(chart_def.data)
        if isinstance(chart_def.hue, list):
            hue_col_name = "hue"
            suffix = 0
            while hue_col_name in data_dict:
                suffix += 1
                hue_col_name = f"hue_{suffix}"
            data_dict[hue_col_name] = chart_def.hue
            kwargs["hue"] = hue_col_name

        if data_dict:
            list_lengths = [len(v) for v in data_dict.values() if isinstance(v, list)]
            if list_lengths:
                min_len = min(list_lengths)
                if any(len(v) != min_len for v in data_dict.values() if isinstance(v, list)):
                    for k, v in list(data_dict.items()):
                        if isinstance(v, list):
                            data_dict[k] = v[:min_len]
                    logger.warning("Truncated chart data series to min length %d", min_len)

        if kind in ("heatmap", "clustermap", "pair", "pair_kde") and "columns" in data_dict:
            if chart_def.columns is None:
                chart_def.columns = data_dict.pop("columns")
            else:
                data_dict.pop("columns", None)

        # Heatmap and clustermap can accept a direct matrix as a single nested list.
        if kind in ("heatmap", "clustermap") and len(data_dict) == 1:
            matrix = next(iter(data_dict.values()))
            if isinstance(matrix, list) and matrix and isinstance(matrix[0], list):
                if chart_def.columns is not None:
                    df = pd.DataFrame(matrix, columns=chart_def.columns)
                    kwargs["columns"] = chart_def.columns
                else:
                    df = pd.DataFrame(matrix)
                kwargs["matrix"] = True
            else:
                df = pd.DataFrame(data_dict)
        else:
            df = pd.DataFrame(data_dict)
        if chart_def.x is not None:
            kwargs["x"] = chart_def.x
        elif "x" in df.columns:
            kwargs["x"] = "x"
        elif kind in ("hist", "kde", "ecdf", "ridge", "boxen", "bar", "count", "point", "box", "violin", "strip", "swarm", "line", "timeseries"):
            kwargs["x"] = df.columns[0]
        if chart_def.y is not None:
            kwargs["y"] = chart_def.y
        elif "y" in df.columns:
            kwargs["y"] = "y"
        if chart_def.size is not None:
            kwargs["size"] = chart_def.size
        elif chart_def.z is not None:
            kwargs["size"] = chart_def.z
        elif kind == "bubble" and "size" in df.columns:
            kwargs["size"] = "size"
        if chart_def.col is not None:
            kwargs["col"] = chart_def.col
        elif kind in ("lmplot_facet", "timeseries_facet") and "col" in df.columns:
            kwargs["col"] = "col"
        if chart_def.columns is not None:
            kwargs["columns"] = chart_def.columns

        if chart_def.x is not None and chart_def.x not in df.columns:
            raise ValueError(f"chart x column {chart_def.x!r} not found in chart.data")
        if chart_def.y is not None and chart_def.y not in df.columns:
            raise ValueError(f"chart y column {chart_def.y!r} not found in chart.data")
        if chart_def.group is not None and chart_def.group not in df.columns:
            raise ValueError(f"chart group column {chart_def.group!r} not found in chart.data")
        if chart_def.size is not None and chart_def.size not in df.columns:
            raise ValueError(f"chart size column {chart_def.size!r} not found in chart.data")
        if chart_def.z is not None and chart_def.z not in df.columns:
            raise ValueError(f"chart z size alias column {chart_def.z!r} not found in chart.data")
        if chart_def.col is not None and chart_def.col not in df.columns:
            raise ValueError(f"chart col column {chart_def.col!r} not found in chart.data")

        if kind == "ridge" and "group" not in kwargs and "group" in df.columns:
            kwargs["group"] = "group"
        if kind in ("lmplot_facet", "timeseries_facet") and "col" not in kwargs:
            raise ValueError(f"{kind} charts require a col field and a matching data column to facet by")

        if kind in ("bar", "box", "violin", "strip", "swarm", "point") and "y" not in kwargs:
            raise ValueError(
                f"{kind} charts require both x and y series in chart.data, e.g. {{x: [...], y: [...]}}"
            )
        if kind == "bubble" and "size" not in kwargs:
            raise ValueError(
                "bubble charts require a size series, for example {size: 'column_name'} or {z: 'column_name'}"
            )
        if kind == "count" and "x" not in kwargs:
            raise ValueError(
                "count charts require an x series in chart.data, for example {x: ['A','B','A']}"
            )
        if kind == "count" and "x" not in kwargs:
            raise ValueError(
                "count charts require an x series in chart.data, for example {x: ['A','B','A']}"
            )
    else:
        if kind in ("bar", "line", "pie"):
            if chart_def.categories is None or chart_def.values is None:
                raise ValueError(f"{kind} charts require categories and values when data is absent.")
            df = pd.DataFrame({"category": chart_def.categories, "value": chart_def.values})
            kwargs["x"] = "category"
            kwargs["y"] = "value"
        elif kind == "hist":
            if not chart_def.values:
                raise ValueError("Histogram requires values when data is absent.")
            df = pd.DataFrame({"value": chart_def.values})
            kwargs["x"] = "value"
        elif kind == "scatter":
            if isinstance(chart_def.x, list) and isinstance(chart_def.y, list):
                if len(chart_def.x) != len(chart_def.y):
                    raise ValueError("Scatter x and y lists must have the same length.")
                df = pd.DataFrame({"x": chart_def.x, "y": chart_def.y})
                kwargs["x"] = "x"
                kwargs["y"] = "y"
            else:
                raise ValueError("Scatter requires x and y lists when data is absent.")
        else:
            raise ValueError("chart data is required for matplotlib rendering.")

    from matplotlib import pyplot as plt

    buf = BytesIO()
    kwargs["save_path"] = buf
    result = chart(kind, df, **kwargs)

    if hasattr(result, "figure"):
        plt.close(result.figure)
    elif isinstance(result, tuple):
        first = result[0]
        if hasattr(first, "figure"):
            plt.close(first.figure)
        elif isinstance(first, plt.Figure):
            plt.close(first)
        else:
            plt.close('all')
    elif isinstance(result, plt.Figure):
        plt.close(result)
    else:
        plt.close('all')

    buf.seek(0)
    return buf


def add_chart(slide, chart_def: ChartData, left, top, width, height,
              accent_rgb: RGBColor = None, bg_rgb: RGBColor = None,
              txt_color: RGBColor = None):
    """Render charts using the matplotlib backend and insert the image into PowerPoint."""
    chart_image = _render_chart_image(chart_def, width, height)
    place_image_centered(slide, chart_image, left, top, width, height)
    return

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
    dpi: int = 300,
) -> BytesIO:
    """Render a list of mathtext strings to a transparent PNG image in memory."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fg = (txt_rgb[0] / 255, txt_rgb[1] / 255, txt_rgb[2] / 255)
    n = max(len(latex_lines), 1)
    fig_h = max(1.5, n * 0.85)
    fig, ax = plt.subplots(figsize=(10, fig_h), dpi=dpi)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    for i, raw_line in enumerate(latex_lines):
        line = _sanitize_latex_line(raw_line).strip()
        if line and not (line.startswith('$') and line.endswith('$')):
            line = f'${line}$'
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
                 sanitize_slide_text(data.text, preserve_markdown=True), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 text_style=data.text_style)
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
                  config.font_heading, config.font_body, txt_color, accent,
                  data.left.text_style)
    _build_column(slide, MARGIN + col_w + gutter, content_top, col_w, content_h,
                  sanitize_slide_text(data.right.title), data.right.text,
                  config.font_heading, config.font_body, txt_color, accent,
                  data.right.text_style)
    _add_notes(slide, data.notes)


def _build_column(slide, left, top, width, height,
                  title, text, font_heading, font_body, txt_color, accent,
                  text_style: Literal["prose", "bullets"] = "prose"):
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
                 sanitize_slide_text(text, preserve_markdown=True), font_body, 13,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 text_style=text_style)


def build_content_mixed(prs, config: GlobalConfig, data: ContentMixedSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, data.header_bar, bg_rgb)
    content_top += Inches(0.3)
    gutter = Inches(0.4)
    total_inner_w = W - MARGIN * 2 - gutter
    text_col_w = int(total_inner_w * 0.38)
    right_col_w = total_inner_w - text_col_w
    add_text_box(slide, MARGIN, content_top, text_col_w, H - content_top - MARGIN,
                 sanitize_slide_text(data.text or '', preserve_markdown=True), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 text_style=data.text_style,
                 accent_rgb=accent, bg_rgb=bg_rgb)
    right_x = MARGIN + text_col_w + gutter
    if data.image_id:
        img_source = _resolve_image(image_registry, data.image_id)
        img_top = content_top + Inches(0.08)
        img_height = H - content_top - MARGIN - Inches(0.16)
        place_image_centered(slide, img_source, right_x, img_top, right_col_w, img_height)
    elif data.chart:
        add_chart(slide, data.chart, right_x, content_top, right_col_w, H - content_top - MARGIN,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color)
    elif data.table:
        add_table(slide, data.table, right_x, content_top + Inches(0.1), right_col_w,
                  H - content_top - MARGIN - Inches(0.1), config.font_body,
                  accent_rgb=accent, bg_rgb=bg_rgb, txt_color=txt_color)
    _add_notes(slide, data.notes)


def build_timeline(prs, config: GlobalConfig, data: TimelineSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    content_top = _add_accent_title_bar(slide, prs, data.title, config.font_heading, accent, txt_color, True, bg_rgb)
    content_top += Inches(0.3)

    items = data.items
    n_items = len(items)
    active_idx = data.active_index if data.active_index is not None else n_items // 2
    usable_w = W - MARGIN * 2
    step = usable_w / max(n_items - 1, 1)

    # Center the timeline vertically below the header, keeping room for event labels above and below.
    line_y = int(round(H * 0.48))
    line_top = line_y - int(round(Inches(0.02)))
    add_rect(slide, MARGIN, line_top, usable_w, Inches(0.04), fill_color=RGBColor(0xCB, 0xD5, 0xE1))

    base_radius = Inches(0.32)
    active_radius = Inches(0.58)
    inner_radius = Inches(0.22)
    active_inner_radius = Inches(0.28)
    text_box_width = Inches(2.6)
    text_box_height = Inches(0.90)

    for i, item in enumerate(items):
        x = int(round(MARGIN + i * step))
        active = (i == active_idx)
        radius = active_radius if active else base_radius
        circle_fill = accent if active else RGBColor(0x06, 0x5A, 0x82)
        circle_border = accent if active else RGBColor(0x1C, 0x72, 0x93)
        inner_r = active_inner_radius if active else inner_radius

        add_oval_shape(slide, x - radius, line_y - radius, radius * 2, radius * 2,
                       fill_color=circle_fill, line_color=circle_border, line_w_pt=2.5)

        inner_shape = add_oval_shape(slide, x - inner_r, line_y - inner_r,
                                     inner_r * 2, inner_r * 2,
                                     fill_color=RGBColor(255, 255, 255), line_color=None)
        if item.emoji:
            tf = inner_shape.text_frame
            tf.clear()
            tf.margin_bottom = 0
            tf.margin_top = 0
            tf.margin_left = 0
            tf.margin_right = 0
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = item.emoji
            run.font.name = config.font_body
            run.font.size = Pt(24 if active else 20)
            run.font.bold = True

        is_top = (i % 2 == 0)
        edge_padding = Inches(0.40)
        if i == 0:
            text_left = max(int(round(MARGIN - edge_padding)), int(round(x - text_box_width + Inches(0.12))))
            text_align = PP_ALIGN.LEFT
        elif i == n_items - 1:
            text_left = min(int(round(W - MARGIN - text_box_width + edge_padding)), int(round(x - Inches(0.12))))
            text_align = PP_ALIGN.RIGHT
        else:
            text_left = int(round(x - text_box_width / 2))
            text_left = max(int(round(MARGIN)), min(int(round(W - MARGIN - text_box_width)), text_left))
            text_align = PP_ALIGN.CENTER

        if is_top:
            text_top = int(round(line_y - radius * 2 - text_box_height - Inches(0.18)))
            connector_start_y = int(round(line_y - radius))
            connector_end_y = int(round(text_top + text_box_height))
        else:
            text_top = int(round(line_y + radius * 2 + Inches(0.18)))
            connector_start_y = int(round(line_y + radius))
            connector_end_y = text_top

        add_line_shape(slide, x, connector_start_y, x, connector_end_y, color=circle_fill, width_pt=1.5, dash=True)

        add_text_box(slide, text_left, text_top, text_box_width, Inches(0.28),
                     item.fecha, config.font_body, 10, color=circle_border, bold=True, align=text_align)
        add_text_box(slide, text_left, text_top + Inches(0.28), text_box_width, Inches(0.62),
                     item.titulo, config.font_body, 13, color=txt_color, bold=True, align=text_align, word_wrap=True)

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
                 sanitize_slide_text(data.text, preserve_markdown=True), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                 text_style=data.text_style,
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
                     sanitize_slide_text(data.text, preserve_markdown=True), config.font_body, 15,
                     color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                     text_style=data.text_style)
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN + col_w + gutter, content_top, col_w, content_h, valign="top")
    else:
        # Full layout: optional intro text above, then full-width equations image
        if data.text:
            text_h = Inches(0.65)
            add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, text_h,
                         sanitize_slide_text(data.text, preserve_markdown=True), config.font_body, 14,
                         color=txt_color, align=PP_ALIGN.LEFT, word_wrap=True, markdown=True,
                         text_style=data.text_style)
            content_top += text_h + Inches(0.15)
            content_h = H - content_top - MARGIN
        latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
        place_image_centered(slide, latex_img, MARGIN, content_top, W - MARGIN * 2, content_h, valign="top")
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
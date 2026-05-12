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
    type: Literal["bar", "pie", "scatter"]
    title: Optional[str] = None
    categories: Optional[List[str]] = None
    values: Optional[List[float]] = None
    x: Optional[List[float]] = None
    y: Optional[List[float]] = None

    @model_validator(mode="after")
    def validate_chart(self):
        if self.type in ("bar", "pie"):
            if not self.categories or not self.values:
                raise ValueError("Bar and pie charts require categories and values.")
            if len(self.categories) != len(self.values):
                raise ValueError("Categories and values must have the same length.")
        elif self.type == "scatter":
            if not self.x or not self.y:
                raise ValueError("Scatter charts require x and y lists.")
            if len(self.x) != len(self.y):
                raise ValueError("Scatter x and y lists must have the same length.")
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

def sanitize_slide_text(text: str) -> str:
    """Strip markdown formatting and inline LaTeX from plain slide text.

    Removes:
    - Inline LaTeX: $...$ and $$...$$ (replaced by the inner raw text without $ delimiters)
    - Bold/italic markers: **...**, __...__, *...*, _..._
    - Inline code: `...`
    - Setext / ATX heading markers (leading #)
    - Literal escape sequences \\n that models sometimes include
    """
    if not text:
        return text
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
    # Literal \n sequences models sometimes insert
    text = text.replace('\\n', '\n')
    return text


_UNSUPPORTED_MATHTEXT = (
    r'\bigg', r'\Bigg', r'\big', r'\Big',
    r'\left', r'\right',
    r'\mkern', r'\mspace', r'\hspace', r'\vspace',
    r'\text', r'\mathrm', r'\mathit', r'\mathbf',
)

def _sanitize_latex_line(line: str) -> str:
    """Normalize a mathtext line for matplotlib rendering.

    - Converts $$...$$ delimiters to $...$ (matplotlib uses single-dollar mathtext)
    - Collapses over-escaped backslashes (\\\\cmd → \\cmd → \cmd in mathtext)
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


def add_text_box(
    slide,
    left, top, width, height,
    text,
    font_name, font_size,
    bold=False, italic=False,
    color=RGBColor(0, 0, 0),
    align=PP_ALIGN.CENTER,
    word_wrap=True,
):
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = word_wrap
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return shape


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

    picture = slide.shapes.add_picture(
        img_source,
        left + offset_x,
        top + offset_y,
        width=final_w,
        height=final_h,
    )
    return picture


def add_chart(slide, chart_def: ChartData, left, top, width, height):
    if chart_def.type in ("bar", "pie"):
        data = CategoryChartData()
        data.categories = chart_def.categories
        data.add_series(chart_def.title or "Serie", chart_def.values)
        chart_type = (
            XL_CHART_TYPE.COLUMN_CLUSTERED if chart_def.type == "bar"
            else XL_CHART_TYPE.PIE
        )
        slide.shapes.add_chart(chart_type, left, top, width, height, data)
    else:
        xy = XyChartData()
        series = xy.add_series(chart_def.title or "Serie")
        for xv, yv in zip(chart_def.x, chart_def.y):
            series.add_data_point(xv, yv)
        slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, left, top, width, height, xy)


def add_table(slide, table_def: TableData, left, top, width, height, font_name, font_size=12):
    rows = len(table_def.rows) + 1
    cols = len(table_def.headers)
    row_height = Inches(0.45)
    ideal_height = rows * row_height
    actual_height = min(ideal_height, height)
    tbl = slide.shapes.add_table(rows, cols, left, top, width, actual_height).table
    for ci, header in enumerate(table_def.headers):
        cell = tbl.cell(0, ci)
        cell.text = header
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.runs[0] if p.runs else p.add_run()
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = True

    for ri, row_data in enumerate(table_def.rows, start=1):
        for ci, cell_text in enumerate(row_data):
            cell = tbl.cell(ri, ci)
            cell.text = str(cell_text)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.runs[0] if p.runs else p.add_run()
            run.font.name = font_name
            run.font.size = Pt(font_size)


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
    """Render a list of mathtext strings to a PNG image in memory."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    bg = (bg_rgb[0] / 255, bg_rgb[1] / 255, bg_rgb[2] / 255)
    fg = (txt_rgb[0] / 255, txt_rgb[1] / 255, txt_rgb[2] / 255)
    n = max(len(latex_lines), 1)
    fig_h = max(1.5, n * 0.85)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
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
            # Fallback: strip all $ and remaining backslash commands, render as plain text
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
                facecolor=bg, edgecolor='none')
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
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, accent)
    W = prs.slide_width
    inner_w = W - MARGIN * 2
    white = RGBColor(255, 255, 255)
    block_h = Inches(2.8)
    block_top = int((prs.slide_height - block_h) / 2)
    add_text_box(slide, MARGIN, block_top, inner_w, Inches(1.2),
                 data.title, config.font_heading, 44,
                 bold=True, color=white)
    if data.subtitle:
        add_text_box(slide, MARGIN, block_top + Inches(1.3), inner_w, Inches(0.9),
                     data.subtitle, config.font_body, 24,
                     italic=True, color=white)
    if data.date:
        add_text_box(slide, MARGIN, block_top + Inches(2.3), inner_w, Inches(0.6),
                     data.date, config.font_body, 16, color=white)
    _add_notes(slide, data.notes)


def build_content_image(prs, config: GlobalConfig, data: ContentImageSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    if data.header_bar:
        content_top = add_header_bar(slide, prs, data.title, config.font_heading, accent)
    else:
        content_top = MARGIN
        add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, BAR_H,
                     data.title, config.font_heading, 28,
                     bold=True, color=txt_color)
        content_top += BAR_H + Inches(0.1)
    text_h = Inches(0.9)
    add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, text_h,
                 sanitize_slide_text(data.text), config.font_body, 16, color=txt_color)
    img_top = content_top + text_h + Inches(0.15)
    img_area_h = H - img_top - MARGIN
    img_area_w = W - MARGIN * 2
    img_source = _resolve_image(image_registry, data.image_id)
    place_image_centered(slide, img_source, MARGIN, img_top, img_area_w, img_area_h)
    _add_notes(slide, data.notes)


def build_two_column(prs, config: GlobalConfig, data: TwoColumnSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    add_text_box(slide, MARGIN, MARGIN, W - MARGIN * 2, BAR_H,
                 data.title, config.font_heading, 28,
                 bold=True, color=txt_color)
    content_top = MARGIN + BAR_H + Inches(0.15)
    content_h = H - content_top - MARGIN
    gutter = Inches(0.3)
    col_w = int((W - MARGIN * 2 - gutter) / 2)
    left_x = MARGIN
    _build_column(slide, left_x, content_top, col_w, content_h,
                  sanitize_slide_text(data.left.title), sanitize_slide_text(data.left.text),
                  config.font_heading, config.font_body, txt_color, accent)
    sep_x = MARGIN + col_w + int(gutter / 2)
    add_vertical_separator(slide, sep_x, content_top, content_top + content_h, accent)
    right_x = MARGIN + col_w + gutter
    _build_column(slide, right_x, content_top, col_w, content_h,
                  sanitize_slide_text(data.right.title), sanitize_slide_text(data.right.text),
                  config.font_heading, config.font_body, txt_color, accent)
    _add_notes(slide, data.notes)


def _build_column(slide, left, top, width, height,
                  title, text, font_heading, font_body, txt_color, accent):
    title_h = Inches(0.6)
    add_text_box(slide, left, top, width, title_h,
                 title, font_heading, 18,
                 bold=True, color=txt_color, align=PP_ALIGN.LEFT)
    body_top = top + title_h + Inches(0.1)
    body_h = height - title_h - Inches(0.1)
    add_text_box(slide, left, body_top, width, body_h,
                 text, font_body, 14,
                 color=txt_color, align=PP_ALIGN.JUSTIFY)


def build_content_mixed(prs, config: GlobalConfig, data: ContentMixedSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    if data.header_bar:
        content_top = add_header_bar(slide, prs, data.title, config.font_heading, accent)
    else:
        content_top = MARGIN
        add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, BAR_H,
                     data.title, config.font_heading, 28,
                     bold=True, color=txt_color)
        content_top += BAR_H + Inches(0.1)
    gutter = Inches(0.3)
    col_w = int((W - MARGIN * 2 - gutter) / 2)
    content_h = H - content_top - MARGIN
    add_text_box(slide, MARGIN, content_top, col_w, content_h,
                 sanitize_slide_text(data.text or ""), config.font_body, 15,
                 color=txt_color, align=PP_ALIGN.JUSTIFY)
    sep_x = MARGIN + col_w + int(gutter / 2)
    add_vertical_separator(slide, sep_x, content_top, content_top + content_h, accent)
    right_x = MARGIN + col_w + gutter
    right_w = col_w
    right_h = content_h
    if data.image_id:
        img_source = _resolve_image(image_registry, data.image_id)
        place_image_centered(slide, img_source, right_x, content_top, right_w, right_h)
    elif data.chart:
        add_chart(slide, data.chart, right_x, content_top, right_w, right_h)
    elif data.table:
        add_table(slide, data.table, right_x, content_top, right_w, right_h,
                  config.font_body)
    _add_notes(slide, data.notes)


def build_section_divider(prs, config: GlobalConfig, data: SectionDividerSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, hex_to_rgb(config.accent_color))
    W, H = prs.slide_width, prs.slide_height
    inner_w = W - MARGIN * 2
    white = RGBColor(255, 255, 255)
    block_h = Inches(2.0)
    block_top = int((H - block_h) / 2)
    add_text_box(slide, MARGIN, block_top, inner_w, Inches(1.2),
                 data.title, config.font_heading, 42,
                 bold=True, color=white)
    if data.subtitle:
        add_text_box(slide, MARGIN, block_top + Inches(1.3), inner_w, Inches(0.8),
                     data.subtitle, config.font_body, 24,
                     italic=True, color=white)
    _add_notes(slide, data.notes)


def build_content_text(prs, config: GlobalConfig, data: ContentTextSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    if data.header_bar:
        content_top = add_header_bar(slide, prs, data.title, config.font_heading, accent)
    else:
        content_top = MARGIN
        add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, BAR_H,
                     data.title, config.font_heading, 28,
                     bold=True, color=txt_color)
        content_top += BAR_H + Inches(0.1)
    content_h = H - content_top - MARGIN
    add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, content_h,
                 sanitize_slide_text(data.text), config.font_body, 16,
                 color=txt_color, align=PP_ALIGN.JUSTIFY, word_wrap=True)
    _add_notes(slide, data.notes)


def build_content_latex(prs, config: GlobalConfig, data: ContentLatexSlide, image_registry: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg_rgb, txt_color = _resolve_background(config, data.background)
    accent = hex_to_rgb(config.accent_color)
    set_slide_background(slide, bg_rgb)
    W, H = prs.slide_width, prs.slide_height
    if data.header_bar:
        content_top = add_header_bar(slide, prs, data.title, config.font_heading, accent)
    else:
        content_top = MARGIN
        add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, BAR_H,
                     data.title, config.font_heading, 28,
                     bold=True, color=txt_color)
        content_top += BAR_H + Inches(0.1)
    if data.text:
        text_h = Inches(0.7)
        add_text_box(slide, MARGIN, content_top, W - MARGIN * 2, text_h,
                     data.text, config.font_body, 15, color=txt_color)
        content_top += text_h + Inches(0.1)
    img_area_h = H - content_top - MARGIN
    img_area_w = W - MARGIN * 2
    latex_img = _render_latex_to_image(data.latex_lines, bg_rgb, txt_color)
    place_image_centered(slide, latex_img, MARGIN, content_top, img_area_w, img_area_h)
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
"""Text box and markdown text rendering utilities for the PPTX slide generator."""

import math
import re as _re
from typing import Literal, Optional

from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from tools.pptx.models import TableData

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

_INLINE_BULLET_SEP = _re.compile(r'(?<=[.;:])\s+-\s+(?=\S)')

_UNSUPPORTED_MATHTEXT = (
    r'\bigg', r'\Bigg', r'\big', r'\Big',
    r'\left', r'\right',
    r'\mkern', r'\mspace', r'\hspace', r'\vspace',
    r'\mathrm', r'\mathit', r'\mathbf',
)


def _split_inline_dash_bullets(text: str) -> str:
    """Convert inline dash-separated clauses like 'A. - B. - C.' into separate bullet lines."""
    lines = text.split('\n')
    out_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or _re.match(r'^(\s*[-*•]|\s*\d+\.)\s+', stripped):
            out_lines.append(line)
            continue
        parts = _INLINE_BULLET_SEP.split(stripped)
        if len(parts) > 1:
            out_lines.append('- ' + parts[0])
            out_lines.extend('- ' + p for p in parts[1:])
        else:
            out_lines.append(line)
    return '\n'.join(out_lines)


def sanitize_slide_text(text: str, preserve_markdown: bool = False) -> str:
    """Strip markdown formatting and inline LaTeX from plain slide text."""
    if not text:
        return text
    text = text.replace('\\n', '\n')
    text = _re.sub(r'\$\$(.+?)\$\$', lambda m: m.group(1).strip(), text, flags=_re.DOTALL)
    text = _re.sub(r'\$(.+?)\$', lambda m: m.group(1).strip(), text)
    if not preserve_markdown:
        text = _re.sub(r'[*_]{3}(.+?)[*_]{3}', r'\1', text)
        text = _re.sub(r'[*_]{2}(.+?)[*_]{2}', r'\1', text)
        text = _re.sub(r'[*_](.+?)[*_]', r'\1', text)
        text = _re.sub(r'`(.+?)`', r'\1', text)
    text = _re.sub(r'^#{1,6}\s+', '', text, flags=_re.MULTILINE)
    for cmd, uni in _LATEX_CMD_TO_UNICODE.items():
        text = text.replace(cmd, uni)
    text = _re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = _re.sub(r'\\[a-zA-Z]+', '', text)
    text = _split_inline_dash_bullets(text)
    return text


def _sanitize_latex_line(line: str) -> str:
    r"""Normalize a mathtext line for matplotlib rendering."""
    if not line:
        return line
    line = line.replace('$$', '$')
    line = _re.sub(r'\*\*(.+?)\*\*', r'\\mathbf{\1}', line)
    line = _re.sub(r'\*(.+?)\*', r'\\mathit{\1}', line)
    while '\\\\' in line:
        line = line.replace('\\\\', '\\')
    for cmd in _UNSUPPORTED_MATHTEXT:
        line = line.replace(cmd, '')
    return line


def _parse_inline_markdown(text: str):
    """Parse inline markdown and return list of (segment_text, bold, italic) tuples."""
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


def _parse_md_table(table_lines: list) -> Optional[TableData]:
    """Parse a list of markdown table lines (header, separator, rows) into TableData."""
    if len(table_lines) < 2:
        return None

    def split_row(line):
        """Split a Markdown table row into trimmed cell strings."""
        return [c.strip() for c in line.strip().strip('|').split('|')]

    headers = split_row(table_lines[0])
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
    """Split markdown text into segments: ('text', str) or ('table', TableData)."""
    lines = text.splitlines()
    segments = []
    current_lines: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
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
        p.line_spacing = 1.25
        p.space_after = Pt(10)
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


def _autofit_font_size(text: str, base_size: int, width_emu: int, height_emu: int) -> int:
    """Estimate the largest font size at which text fits in the given box."""
    width_in = max(width_emu / 914400.0, 0.5)
    height_in = max(height_emu / 914400.0, 0.5)
    lines = (text or "").replace("\\n", "\n").splitlines()
    n_paras = max(1, len([l for l in lines if l.strip()]))
    size = base_size
    while size > 9:
        chars_per_line = max(1, int(width_in * 142 / size))
        wrapped = 0.0
        for l in lines:
            s = l.strip()
            wrapped += math.ceil(len(s) / chars_per_line) if s else 0.5
        total_in = wrapped * (size * 1.25) / 72.0 + n_paras * (10 / 72.0)
        if total_in <= height_in:
            break
        size -= 1
    return size


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
    vertical_center: bool = False,
    autofit: bool = False,
):
    """Add a text box. markdown=True parses bold/italic/bullets.
    text_style='bullets' forces every non-empty line into a bullet item.
    Embedded markdown pipe tables are automatically detected and rendered as real PPTX tables.
    """
    if text and text_style == "bullets":
        text = _force_bullet_text(text)

    if autofit and text:
        _base_size = font_size
        font_size = _autofit_font_size(text, font_size, width, height)
        if font_size < _base_size:
            vertical_center = False

    def _apply_autofit(tf):
        if autofit:
            tf.word_wrap = True
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

    if not markdown or not text:
        shape = slide.shapes.add_textbox(left, top, width, height)
        shape.text_frame.word_wrap = word_wrap
        if vertical_center:
            shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        shape.text_frame.clear()
        p = shape.text_frame.paragraphs[0]
        p.alignment = align
        _add_run_to_paragraph(p, text or '', font_name, font_size, bold, italic, color)
        _apply_autofit(shape.text_frame)
        return shape

    segments = _split_text_and_tables(text.replace('\\n', '\n'))
    has_table = any(seg_type == 'table' for seg_type, _ in segments)

    if not has_table:
        shape = slide.shapes.add_textbox(left, top, width, height)
        shape.text_frame.word_wrap = word_wrap
        if vertical_center:
            shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        shape.text_frame.clear()
        _fill_textbox_markdown(shape.text_frame, text, font_name, font_size,
                               bold, italic, color, align)
        _apply_autofit(shape.text_frame)
        return shape

    # Mixed text + table: stack segments vertically within the given bounds
    # Late import to avoid circular dependency (shapes imports text, text imports shapes)
    from tools.pptx.shapes import add_table

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

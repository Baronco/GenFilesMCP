"""Parser that converts a YAML string into a validated DocxBodyElements object."""

import re
from typing import Any

import yaml
from pydantic import ValidationError

from utils.config.logger import get_logger
from utils.models.arguments import (
    Cover,
    ElemEquation,
    ElemHeader,
    ElemImage,
    ElemList,
    ElemPageBreak,
    ElemParagraph,
    ElemTable,
)
from utils.models.endpoints import DocxBodyElements

logger = get_logger(__name__)

_STYLE_COLUMNS = {"ieee": 2, "report": 1}
_DEFAULT_STYLE = "report"

_LATEX_DQ_RE = re.compile(r'(?P<pre>(?:^|[\s{,])latex\s*:\s*)"(?P<val>[^"\n]*)"')

_LATEX_HINT = (
    " Hint: put any value containing backslashes (e.g. a LaTeX equation) in SINGLE quotes so "
    "YAML keeps the backslashes literal — e.g.  latex: '\\theta - \\alpha \\cdot \\nabla J(\\theta)' . "
    "In DOUBLE quotes, sequences like \\c, \\n, \\t are read as escapes and break the YAML."
)


def _coerce_latex_double_quotes(text: str) -> str:
    """Rewrite double-quoted ``latex:`` scalars as single-quoted to preserve backslashes.

    Args:
        text: Raw YAML string that may contain double-quoted latex values.

    Returns:
        Modified YAML string with latex values in single quotes.
    """
    def _repl(match: "re.Match") -> str:
        val = match.group("val").replace("'", "''")
        return f"{match.group('pre')}'{val}'"
    return _LATEX_DQ_RE.sub(_repl, text)


_ELEMENT_MODEL_MAP = {
    "paragraph": ElemParagraph,
    "paragraphbody": ElemParagraph,
    "header": ElemHeader,
    "paragraphheader": ElemHeader,
    "list": ElemList,
    "paragraphlistitem": ElemList,
    "table": ElemTable,
    "image": ElemImage,
    "equation": ElemEquation,
    "page_break": ElemPageBreak,
    "pagebreak": ElemPageBreak,
}


def _validate_element(raw_element: Any) -> Any:
    """Validate a single raw YAML element dict against its Pydantic model.

    Args:
        raw_element: Raw dict from the parsed YAML body list.

    Returns:
        Validated Pydantic model instance.

    Raises:
        ValueError: If the element type is missing, unrecognized, or fails validation.
    """
    if not isinstance(raw_element, dict):
        raise ValueError("Each item in 'body' must be an object with a 'type' field.")

    element_type = raw_element.get("type")

    if not (isinstance(element_type, str) and element_type.strip()) and len(raw_element) == 1:
        only_key = next(iter(raw_element))
        if isinstance(only_key, str):
            normalized_key = only_key.strip().lower().replace(" ", "_")
            if normalized_key in _ELEMENT_MODEL_MAP:
                inner = raw_element[only_key]
                raw_element = {"type": normalized_key, **inner} if isinstance(inner, dict) else {"type": normalized_key}
                element_type = normalized_key

    if not isinstance(element_type, str) or not element_type.strip():
        raise ValueError("Each body element must include a non-empty 'type' field.")

    normalized_type = element_type.strip().lower().replace(" ", "_")
    model = _ELEMENT_MODEL_MAP.get(normalized_type)
    if model is None:
        supported = ", ".join(sorted(_ELEMENT_MODEL_MAP.keys()))
        raise ValueError(
            f"Unrecognized element type '{element_type}'. Supported types: {supported}."
        )

    try:
        return model.model_validate(raw_element)
    except ValidationError as validation_error:
        raise ValueError(
            f"Element validation failed for type '{element_type}': {validation_error}"
        )


def parse_yaml_to_docx_body(document_yaml: str, file_name: str) -> DocxBodyElements:
    """Parse a YAML string and return a validated DocxBodyElements instance.

    Args:
        document_yaml: Raw YAML string describing cover, style_doc, and body elements.
        file_name: Target filename for the generated DOCX (used in the returned model).

    Returns:
        Validated DocxBodyElements ready for the document builder.

    Raises:
        ValueError: If YAML parsing fails or required fields are invalid.
    """
    document_yaml = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', document_yaml)
    try:
        parsed = yaml.safe_load(document_yaml)
    except yaml.YAMLError as yaml_error:
        coerced = _coerce_latex_double_quotes(document_yaml)
        if coerced != document_yaml:
            try:
                parsed = yaml.safe_load(coerced)
                logger.info("Recovered YAML parse after coercing double-quoted latex to single quotes.")
            except yaml.YAMLError:
                raise ValueError(f"YAML parse error: {yaml_error}.{_LATEX_HINT}")
        else:
            raise ValueError(f"YAML parse error: {yaml_error}.{_LATEX_HINT}")

    if not isinstance(parsed, dict):
        raise ValueError("YAML content must be a mapping with top-level keys like 'style_doc', 'cover', and 'body'.")

    cover_data = parsed.get("cover")
    if cover_data is None:
        raise ValueError("YAML must include a top-level 'cover' section.")
    if not isinstance(cover_data, dict):
        raise ValueError("'cover' must be an object with cover metadata.")

    style_doc = parsed.get("style_doc", _DEFAULT_STYLE)
    if not isinstance(style_doc, str):
        style_doc = _DEFAULT_STYLE
    style_doc = style_doc.strip().lower()
    if style_doc not in _STYLE_COLUMNS:
        logger.warning("Unknown style_doc '%s'; using default '%s'.", style_doc, _DEFAULT_STYLE)
        style_doc = _DEFAULT_STYLE
    columns_body = _STYLE_COLUMNS[style_doc]
    if "columns_body" in parsed:
        logger.info("Legacy 'columns_body' is ignored; layout follows style_doc '%s'.", style_doc)

    body_elements = parsed.get("body", [])
    if body_elements is None:
        body_elements = []
    if not isinstance(body_elements, list):
        raise ValueError("'body' must be a YAML list of document elements.")

    try:
        cover = Cover.model_validate(cover_data)
    except ValidationError as validation_error:
        raise ValueError(f"Cover validation failed: {validation_error}")

    validated_elements = [_validate_element(item) for item in body_elements]

    return DocxBodyElements(
        document_cover=cover,
        style_doc=style_doc,
        columns_body=columns_body,
        document_elements=validated_elements,
        file_name=file_name,
    )

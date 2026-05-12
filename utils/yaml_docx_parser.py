from typing import Any
import re

import yaml
from pydantic import ValidationError

from utils.pydantic_models_arguments import (
    Cover,
    ElemHeader,
    ElemParagraph,
    ElemList,
    ElemTable,
    ElemImage,
    ElemEquation,
    ElemPageBreak,
)
from utils.pydantic_models_endpoints import DocxBodyElements


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
    if not isinstance(raw_element, dict):
        raise ValueError("Each item in 'body' must be an object with a 'type' field.")

    element_type = raw_element.get("type")
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
    # Strip YAML-illegal control characters that models sometimes inject
    document_yaml = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', document_yaml)
    try:
        parsed = yaml.safe_load(document_yaml)
    except yaml.YAMLError as yaml_error:
        raise ValueError(f"YAML parse error: {yaml_error}")

    if not isinstance(parsed, dict):
        raise ValueError("YAML content must be a mapping with top-level keys like 'cover', 'columns_body', and 'body'.")

    cover_data = parsed.get("cover")
    if cover_data is None:
        raise ValueError("YAML must include a top-level 'cover' section.")
    if not isinstance(cover_data, dict):
        raise ValueError("'cover' must be an object with cover metadata.")

    columns_body = parsed.get("columns_body", 1)
    if isinstance(columns_body, str) and columns_body.isdigit():
        columns_body = int(columns_body)
    if not isinstance(columns_body, int):
        raise ValueError("'columns_body' must be an integer.")

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
        columns_body=columns_body,
        document_elements=validated_elements,
        file_name=file_name,
    )


from json import dumps
from typing import Dict, List, Union
from utils.logger import get_logger
from utils.pydantic_models_endpoints import DocxBodyElements

logger = get_logger(__name__)

def _as_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if isinstance(value, dict):
        return value
    try:
        return dict(value)
    except Exception:
        return {}


def _normalize_legacy_element(raw):
    if raw.get("paragraph") is not None and raw.get("header") is None and raw.get("list_item") is None and raw.get("table") is None and raw.get("image") is None and raw.get("equation") is None:
        paragraph = _as_dict(raw["paragraph"])
        text = paragraph.get("text")
        if not text:
            return {"error": "ParagraphBody element requires 'paragraph.text'."}
        return {"type": "ParagraphBody", "text": text}

    if raw.get("header") is not None and raw.get("paragraph") is None and raw.get("list_item") is None and raw.get("table") is None and raw.get("image") is None and raw.get("equation") is None:
        header = _as_dict(raw["header"])
        text = header.get("text")
        level = header.get("level")
        if not text or level is None:
            return {"error": "ParagraphHeader element requires 'header.text' and 'header.level'."}
        return {"type": "ParagraphHeader", "text": text, "level": level}

    if raw.get("list_item") is not None and raw.get("paragraph") is None and raw.get("header") is None and raw.get("table") is None and raw.get("image") is None and raw.get("equation") is None:
        list_item = _as_dict(raw["list_item"])
        items = list_item.get("items")
        list_style = list_item.get("list_style")
        if not items:
            return {"error": "ParagraphListItem element requires 'list_item.items'."}
        if isinstance(items, str):
            items = [line.strip() for line in items.splitlines() if line.strip()]
        if not isinstance(items, list) or not items or any(not isinstance(i, str) or not i.strip() for i in items):
            return {"error": "ParagraphListItem 'items' must be a non-empty list of strings."}
        if list_style not in ("List Number", "List Bullet"):
            list_style = "List Bullet"
        return {"type": "ParagraphListItem", "list_style": list_style, "items": [i.strip() for i in items]}

    if raw.get("table") is not None and raw.get("paragraph") is None and raw.get("header") is None and raw.get("list_item") is None and raw.get("image") is None and raw.get("equation") is None:
        table = _as_dict(raw["table"])
        headers = table.get("table_headers")
        rows = table.get("table_rows")
        caption = table.get("caption", "")
        if not headers or not rows:
            return {"error": "Table element requires 'table_headers' and 'table_rows'."}
        return {"type": "Table", "table_headers": headers, "table_rows": rows, "caption": caption}

    if raw.get("image") is not None and raw.get("paragraph") is None and raw.get("header") is None and raw.get("list_item") is None and raw.get("table") is None and raw.get("equation") is None:
        image = _as_dict(raw["image"])
        image_id = image.get("id")
        caption = image.get("caption", "")
        if not image_id:
            return {"error": "Image element requires 'image.id'."}
        return {"type": "Image", "id": image_id, "caption": caption}

    if raw.get("equation") is not None and raw.get("paragraph") is None and raw.get("header") is None and raw.get("list_item") is None and raw.get("table") is None and raw.get("image") is None:
        equation = _as_dict(raw["equation"])
        latex = equation.get("latex")
        caption = equation.get("caption", "")
        if not latex:
            return {"error": "Equation element requires 'equation.latex'."}
        return {"type": "Equation", "latex": latex, "caption": caption}

    return {"error": "Element has an unrecognized structure or more than one type defined."}


def _normalize_flat_element(raw):
    element_type = raw.get("type")
    if element_type in ("ParagraphBody", "paragraph"):
        text = raw.get("text") or raw.get("content") or raw.get("body")
        if not isinstance(text, str) or not text.strip():
            paragraph = _as_dict(raw.get("paragraph"))
            text = paragraph.get("text")
        if not isinstance(text, str) or not text.strip():
            return {"error": "ParagraphBody element requires a non-empty 'text' field."}
        return {"type": "ParagraphBody", "text": text.strip()}

    if element_type in ("ParagraphHeader", "header"):
        text = raw.get("text")
        level = raw.get("level")
        if level is None:
            header = _as_dict(raw.get("header"))
            level = header.get("level")
        if isinstance(level, str) and level.isdigit():
            level = int(level)
        if not isinstance(text, str) or not text.strip() or level not in (1, 2, 3, 4, 5, 6):
            return {"error": "ParagraphHeader element requires a valid 'text' and numeric 'level' between 1 and 6."}
        return {"type": "ParagraphHeader", "text": text.strip(), "level": level}

    if element_type in ("ParagraphListItem", "list"):
        items = raw.get("items")
        if isinstance(items, str):
            items = [line.strip() for line in items.splitlines() if line.strip()]
        list_style = raw.get("list_style") or raw.get("style") or "List Bullet"
        if list_style == "bullet":
            list_style = "List Bullet"
        elif list_style == "numbered":
            list_style = "List Number"
        if not isinstance(items, list) or not items or any(not isinstance(i, str) or not i.strip() for i in items):
            return {"error": "ParagraphListItem element requires a non-empty list of string items."}
        return {"type": "ParagraphListItem", "list_style": list_style, "items": [i.strip() for i in items]}

    if element_type in ("Table", "table"):
        headers = raw.get("table_headers") or raw.get("headers")
        rows = raw.get("table_rows") or raw.get("rows")
        caption = raw.get("caption", "")
        if not headers or not rows:
            return {"error": "Table element requires 'table_headers' and 'table_rows'."}
        return {"type": "Table", "table_headers": headers, "table_rows": rows, "caption": caption}

    if element_type in ("Image", "image"):
        image_id = raw.get("id") or raw.get("image_id")
        caption = raw.get("caption", "")
        if not isinstance(image_id, str) or not image_id.strip():
            return {"error": "Image element requires a non-empty 'id' field."}
        return {"type": "Image", "id": image_id.strip(), "caption": caption}

    if element_type in ("Equation", "equation"):
        latex = raw.get("latex")
        caption = raw.get("caption", "")
        if not isinstance(latex, str) or not latex.strip():
            return {"error": "Equation element requires a non-empty 'latex' field."}
        return {"type": "Equation", "latex": latex.strip(), "caption": caption}

    if element_type == "page_break":
        return {"type": "page_break"}

    return {"error": f"Unrecognized element type '{element_type}'. Supported types: paragraph, header, list, table, image, equation, page_break, ParagraphBody, ParagraphHeader, ParagraphListItem, Table, Image, Equation."}


def _normalize_element(element):
    raw = _as_dict(element)
    if not isinstance(raw, dict):
        return {"error": "Document element is not a valid object."}
    if "type" not in raw:
        return _normalize_legacy_element(raw)
    return _normalize_flat_element(raw)


def generate_word_template_body_check(body: DocxBodyElements) -> Union[List, Dict]:
    try:
        all_elements = []
        for index, element in enumerate(body.document_elements):
            normalized = _normalize_element(element)
            if isinstance(normalized, dict) and normalized.get("error"):
                return dumps({"error": f"Error in document_elements[{index}]: {normalized['error']}"}, ensure_ascii=False)
            all_elements.append(normalized)
        return all_elements
    except Exception as e:
        logger.error(f"Error processing document elements: {e}")
        return {"error": "An error occurred while processing the document elements. Please check the structure of your input."}

"""Word document generation routes (structured YAML or Python script)."""

from json import dumps
from os import getenv
from typing import Annotated, List

from fastapi import APIRouter, Body, Request

from api.shared import build_request_context, render_download_button_html
from tools.docx_tool import generate_word as _generate_word
from tools.docx_tool import generate_word_from_template as _generate_word_from_template
from utils.builders.docx_element_validator import validate_docx_elements
from utils.builders.yaml_docx_parser import parse_yaml_to_docx_body
from utils.config.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.config.logger import get_logger

OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()
ENABLE_STRUCTURED_YAML_MODE = getenv('ENABLE_STRUCTURED_YAML_MODE', 'false').lower() == 'true'

logger = get_logger(__name__)
router = APIRouter()


async def _generate_word_structured_yaml_handler(
    request: Request,
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    document_yaml: Annotated[str, Body(..., description="Raw YAML text describing the cover, columns_body, and body elements for the document.")],
):
    """Generates a Word document from raw YAML text."""
    logger.info("Received request to generate Word document from YAML")
    try:
        body = parse_yaml_to_docx_body(document_yaml, file_name)
        all_elements = validate_docx_elements(body)
        if isinstance(all_elements, dict) and "error" in all_elements:
            return dumps(all_elements, ensure_ascii=False)

        request_context = build_request_context(request)
        result = _generate_word_from_template(
            body.document_cover,
            body.columns_body,
            all_elements,
            file_name,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            KNOWLEDGE_COLLECTION_NAME,
            style_doc=body.style_doc,
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except ValueError as e:
        logger.error(f"YAML validation error generating Word document: {e}")
        return dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error generating Word document from YAML: {e}")
        return dumps({"error": "An error occurred while generating the Word document from YAML."}, ensure_ascii=False)


async def _generate_word_handler(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = [],
):
    """Generate a Word document using the provided AI-generated Python script."""
    logger.info("Received request to generate Word document")
    try:
        request_context = build_request_context(request)
        result = _generate_word(
            python_script,
            file_name,
            images_list,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            KNOWLEDGE_COLLECTION_NAME
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except Exception as e:
        logger.error(f"Error generating Word document: {e}")
        return dumps({"error": "An error occurred while generating the Word document."}, ensure_ascii=False)


if ENABLE_STRUCTURED_YAML_MODE:
    router.post(
        "/generate_word_structured_yaml",
        summary="Generate Word",
        operation_id="generate_word_structured_yaml",
    )(_generate_word_structured_yaml_handler)
    logger.info("Registered Word endpoint: generate_word_structured_yaml")
else:
    router.post(
        "/generate_word",
        summary="Generate Word",
        operation_id="generate_word",
    )(_generate_word_handler)
    logger.info("Registered Word endpoint: generate_word")

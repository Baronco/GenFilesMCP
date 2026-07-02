"""PowerPoint generation routes (structured YAML or Python script)."""

from json import dumps
from os import getenv
from typing import Annotated, List

from fastapi import APIRouter, Body, Request

from api.shared import build_request_context, render_download_button_html
from tools.pptx import generate_powerpoint as _generate_powerpoint
from tools.pptx import generate_powerpoint_structured_yaml as _generate_powerpoint_structured_yaml
from utils.config.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.config.logger import get_logger

OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()
ENABLE_STRUCTURED_YAML_MODE = getenv('ENABLE_STRUCTURED_YAML_MODE', 'false').lower() == 'true'

logger = get_logger(__name__)
router = APIRouter()


async def _generate_powerpoint_handler(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = [],
):
    """Generates a PowerPoint presentation using a provided Python script."""
    logger.info("Received request to generate PowerPoint presentation")
    try:
        request_context = build_request_context(request)
        result = _generate_powerpoint(
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
        logger.error(f"Error generating PowerPoint presentation: {e}")
        return dumps({"error": "An error occurred while generating the PowerPoint presentation."}, ensure_ascii=False)


async def _generate_powerpoint_structured_yaml_handler(
    request: Request,
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    document_yaml: Annotated[str, Body(..., description="Raw YAML text describing the PowerPoint presentation structure including slides, colors and image references.")],
):
    """Generates a PowerPoint presentation from raw YAML text."""
    logger.info("Received request to generate PowerPoint presentation from YAML")
    try:
        request_context = build_request_context(request)
        result = _generate_powerpoint_structured_yaml(
            document_yaml,
            file_name,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            KNOWLEDGE_COLLECTION_NAME
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except ValueError as e:
        logger.error(f"YAML validation error generating PowerPoint document: {e}")
        return dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error generating PowerPoint document from YAML: {e}")
        return dumps({"error": "An error occurred while generating the PowerPoint document from YAML."}, ensure_ascii=False)


if ENABLE_STRUCTURED_YAML_MODE:
    router.post(
        "/generate_powerpoint_structured_yaml",
        summary="Generate PowerPoint",
        operation_id="generate_powerpoint_structured_yaml",
    )(_generate_powerpoint_structured_yaml_handler)
    logger.info("Registered PowerPoint endpoint: generate_powerpoint_structured_yaml")
else:
    router.post(
        "/generate_powerpoint",
        summary="Generate PowerPoint",
        operation_id="generate_powerpoint",
    )(_generate_powerpoint_handler)
    logger.info("Registered PowerPoint endpoint: generate_powerpoint")

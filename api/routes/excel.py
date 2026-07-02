"""Excel generation route."""

from json import dumps
from os import getenv
from typing import Annotated

from fastapi import APIRouter, Body, Request

from api.shared import build_request_context, render_download_button_html
from tools.excel_tool import generate_excel as _generate_excel
from utils.config.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.config.logger import get_logger

OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/generate_excel",
    summary="Generate Excel",
    operation_id="generate_excel",
)
async def generate_excel(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
):
    """Generates an Excel workbook using a provided Python script."""
    logger.info("Received request to generate Excel workbook")
    try:
        request_context = build_request_context(request)
        result = _generate_excel(
            python_script,
            file_name,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            KNOWLEDGE_COLLECTION_NAME
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except Exception as e:
        logger.error(f"Error generating Excel workbook: {e}")
        return dumps({"error": "An error occurred while generating the Excel workbook."}, ensure_ascii=False)

"""PDF generation route."""

from json import dumps
from os import getenv
from typing import Annotated, List

from fastapi import APIRouter, Body, Request

from api.shared import build_request_context, build_download_response
from tools.pdf_tool import generate_pdf as _generate_pdf
from utils.config.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.config.logger import get_logger

OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/generate_pdf",
    summary="Generate PDF",
    operation_id="generate_pdf",
)
async def generate_pdf(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = [],
):
    """Generates a PDF document using a provided Python script."""
    logger.info("Received request to generate PDF document")
    try:
        request_context = build_request_context(request)
        result = _generate_pdf(
            python_script,
            file_name,
            images_list,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            KNOWLEDGE_COLLECTION_NAME
        )
        return build_download_response(result)
    except Exception as e:
        logger.error(f"Error generating PDF document: {e}")
        return dumps({"error": "An error occurred while generating the PDF document."}, ensure_ascii=False)

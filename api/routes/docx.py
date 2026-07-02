"""DOCX review, listing, and file attachment routes."""

from json import dumps
from os import getenv
from typing import Annotated, List

from fastapi import APIRouter, Body, Request
from requests import get

from api.shared import build_request_context, extract_files_from_chat, render_download_button_html
from tools.docx_tool import full_context_docx as _full_context_docx
from tools.docx_tool import review_docx as _review_docx
from utils.config.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.config.logger import get_logger
from utils.http.authorization import _get_bearer_token
from utils.models.arguments import ReviewComment

OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()
REVIEWER_AI_ASSISTANT_NAME = getenv('REVIEWER_AI_ASSISTANT_NAME', 'GenFilesMCP')

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/list_docx_elements",
    summary="List DOCX Elements",
    operation_id="list_docx_elements",
)
async def full_context_docx(
    request: Request,
    file_id: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["full_context_docx"]["file_id"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["full_context_docx"]["file_name"])],
):
    """Returns the structure of a DOCX document, including index, style, and text of each element."""
    logger.info("Received request to list DOCX document elements")
    try:
        request_context = build_request_context(request)
        return _full_context_docx(file_id, file_name, request_context, OWUI_URL)
    except Exception as e:
        logger.error(f"Error listing DOCX document elements: {e}")
        return dumps({"error": "An error occurred while listing the DOCX document elements."}, ensure_ascii=False)


@router.post(
    "/review_docx",
    summary="Review DOCX Document",
    operation_id="review_docx",
)
async def review_docx(
    request: Request,
    file_id: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_id"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_name"])],
    review_comments: Annotated[List[ReviewComment], Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["review_comments"])],
):
    """Reviews an existing DOCX document and adds comments to specific elements."""
    logger.info("Received request to review DOCX document")
    try:
        request_context = build_request_context(request)
        result = _review_docx(
            file_id,
            file_name,
            review_comments,
            request_context,
            OWUI_URL,
            ENABLE_CREATE_KNOWLEDGE,
            REVIEWER_AI_ASSISTANT_NAME,
            KNOWLEDGE_COLLECTION_NAME
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except Exception as e:
        logger.error(f"Error reviewing DOCX document: {e}")
        return dumps({"error": "An error occurred while reviewing the DOCX document."}, ensure_ascii=False)


@router.get(
    "/fetch_uploaded_chat_file_ids",
    summary="Get Chat Attachments",
    operation_id="fetch_uploaded_chat_file_ids",
)
async def fetch_uploaded_chat_file_ids(request: Request):
    """Returns file IDs of attachments present in the current Open WebUI chat."""
    request_context = build_request_context(request)

    attachments = _get_bearer_token(request_context, chat_headers=True)
    if not isinstance(attachments, dict):
        logger.error("Chat headers were not found or could not be parsed from the request.")
        return dumps({"error": "Unable to retrieve chat headers from the request."}, ensure_ascii=False)

    auth_header = attachments.get('authorization') or attachments.get('Authorization')
    chat_id = attachments.get('x-openwebui-chat-id') or attachments.get('X-Open-WebUI-Chat-Id')

    if not chat_id:
        logger.error("Missing X-Open-WebUI-Chat-Id header in request.")
        return dumps({"error": "Missing chat ID header. Ensure Open WebUI forwards chat headers."}, ensure_ascii=False)

    if not auth_header:
        logger.error("Missing Authorization header for chat API call.")
        return dumps({"error": "Missing Authorization header. Ensure Open WebUI forwards authorization headers."}, ensure_ascii=False)

    endpoint = f"{OWUI_URL.rstrip('/')}/api/v1/chats/{chat_id}"
    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json'
    }

    try:
        response = get(endpoint, headers=headers, timeout=10)

        if response.status_code != 200:
            body_text = response.text.strip()
            logger.error(
                "=> Error retrieving chat details. Status code: %s, body: %s",
                response.status_code,
                body_text[:1000] if body_text else '<empty>'
            )
            return dumps({"error": "An error occurred while retrieving chat attachments."}, ensure_ascii=False)

        try:
            chat_data = response.json()
        except ValueError as json_error:
            logger.error(
                "=> Failed to parse chat response JSON: %s. Response body: %s",
                json_error,
                response.text.strip()[:1000]
            )
            return dumps({"error": "Received invalid JSON from Open WebUI chat endpoint."}, ensure_ascii=False)

        files = extract_files_from_chat(chat_data)
        seen = set()
        unique_files = []
        for f in files:
            fid = f.get("file_id")
            if fid not in seen:
                seen.add(fid)
                unique_files.append(f)

        if len(unique_files) > 0:
            logger.info(f"Extracted {len(unique_files)} unique attachments from chat ({len(files)} total).")
            return dumps({"files_and_images_id": unique_files}, ensure_ascii=False)
        else:
            logger.info("No files or images found in chat.")
            return dumps({"files_and_images_id": "No files or images found in chat."}, ensure_ascii=False)
    except Exception:
        logger.exception("=> Exception retrieving chat details")
        return dumps({"error": "An error occurred while retrieving chat attachments."}, ensure_ascii=False)

# Native libraries
from json import dumps
from os import getenv
from typing import Annotated, Literal, List, Tuple, Union, Any
from pydantic import Field

# Third-party libraries
from fastapi import FastAPI, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from html import escape
import uvicorn

# Utilities
from utils.logger import configure_logging, get_logger
configure_logging()
from utils.load_md_templates import load_md_templates
from utils.register_tools import register_powerpoint_tool, register_word_tool
from utils.argument_descriptions import SERVER_BANNER, MCP_SERVER_NAME, SERVER_VERSION, ARGUMENT_DESCRIPTIONS
from utils.generate_word_template_body_check import generate_word_template_body_check
from utils.pydantic_models_endpoints import DocxBodyElements
from utils.pydantic_models_arguments import Cover, ElementUnion, ReviewComment
from utils.yaml_docx_parser import parse_yaml_to_docx_body

# borrar luego
from utils.authorization import _get_bearer_token
from requests import get
# borrar luego

# Import tools from the tools directory
from tools.powerpoint_tool import generate_powerpoint as _generate_powerpoint, generate_powerpoint_structured_yaml as _generate_powerpoint_structured_yaml
from tools.excel_tool import generate_excel as _generate_excel
from tools.markdown_tool import generate_markdown as _generate_markdown
from tools.docx_tool import full_context_docx as _full_context_docx, review_docx as _review_docx, generate_word_from_template as _generate_word_from_template
from tools.docx_tool import generate_word as _generate_word
from tools.pdf_tool import generate_pdf as _generate_pdf
# Parameters
ENABLE_STRUCTURED_YAML_MODE = getenv('ENABLE_STRUCTURED_YAML_MODE', 'false').lower() == 'true'
OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
PORT = int(getenv('PORT', '8000'))
OWUI_API_KEY = (getenv('OWUI_API_KEY') or '').strip() or None
REVIEWER_AI_ASSISTANT_NAME = getenv('REVIEWER_AI_ASSISTANT_NAME', 'GenFilesMCP')
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()
POWERPOINT_TEMPLATE, EXCEL_TEMPLATE, WORD_TEMPLATE, MARKDOWN_TEMPLATE, PDF_TEMPLATE, MCP_INSTRUCTIONS = load_md_templates(ENABLE_STRUCTURED_YAML_MODE)
ENABLE_CREATE_KNOWLEDGE = getenv('ENABLE_CREATE_KNOWLEDGE', 'true').lower() == 'true'


# Initialize FastAPI server
app = FastAPI(
    title=MCP_SERVER_NAME,
    description=MCP_INSTRUCTIONS,
    version=SERVER_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Logging
logger = get_logger(MCP_SERVER_NAME)


def build_request_context(request: Request) -> dict[str, dict[str, str]]:
    return {"headers": dict(request.headers)}


def get_file_icon_svg(file_type: str) -> str:
    file_type_normalized = (file_type or "").strip().lower()
    color_map = {
        "pdf": "#ef4444",
        "docx": "#60a5fa",
        "pptx": "#fb923c",
        "xlsx": "#22c55e",
        "md": "#7c3aed",
    }
    icon_label_map = {
        "pdf": "PDF",
        "docx": "DOCX",
        "pptx": "PPTX",
        "xlsx": "XLSX",
        "md": "MD",
    }

    icon_label = icon_label_map.get(file_type_normalized, "FILE")
    icon_fill = color_map.get(file_type_normalized, "#6b7280")
    is_long_label = len(icon_label) > 3
    font_size = "8.5" if is_long_label else "12"
    text_attrs = ' textLength="26" lengthAdjust="spacingAndGlyphs"' if is_long_label else ""

    svg = (
        '<svg viewBox="0 0 42 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" style="width:32px;height:26px;">'
        f'<rect x="2" y="2" width="38" height="28" rx="6" fill="{icon_fill}" />'
        '<path d="M8 7h11l4 4v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" fill="#ffffff" fill-opacity="0.12" />'
        f'<text x="21" y="18" text-anchor="middle" dominant-baseline="middle" font-family="Inter, Arial, sans-serif" font-size="{font_size}" font-weight="700" fill="#ffffff"{text_attrs}>{icon_label}</text>'
        '</svg>'
    )
    return svg


def render_download_button_html(result: dict) -> HTMLResponse | None:
    """Return an HTMLResponse with a download button for generated file results."""
    if not isinstance(result, dict):
        return None

    download_url = result.get("download_url")
    file_name = result.get("file_name")
    file_type = result.get("file_type")

    if not download_url or not file_name or not file_type:
        return None

    safe_url = escape(download_url, quote=True)
    safe_name = escape(file_name)
    safe_type = escape(file_type)
    if safe_name.lower().endswith(f".{safe_type.lower()}"):
        safe_download_name = safe_name
    else:
        safe_download_name = f"{safe_name}.{safe_type}"
    display_name = escape(safe_download_name)

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Download file</title>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at top, rgba(37, 99, 235, 0.15), transparent 36%),
                        linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            color: #111827;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px;
        }}
        .download-card {{
            width: min(100%, 420px);
            padding: 18px 18px 16px;
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 24px;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
            text-align: center;
            backdrop-filter: blur(14px);
        }}
        .download-card h1 {{
            font-size: 1.14rem;
            margin: 0 0 14px;
            line-height: 1.25;
            letter-spacing: -0.02em;
        }}
        .download-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.65rem;
            width: 100%;
            padding: 10px 16px;
            color: #ffffff;
            background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
            border-radius: 16px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.96rem;
            transition: transform 0.16s ease, box-shadow 0.16s ease;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
        }}
        .download-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.22);
        }}
        .download-button:active {{
            transform: translateY(0);
        }}
        .download-icon {{
            width: 28px;
            height: 28px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        .file-name {{
            margin: 12px auto 0;
            color: #475569;
            font-size: 0.86rem;
            line-height: 1.4;
            word-break: break-word;
            max-width: 100%;
            opacity: 0.88;
        }}
    </style>
</head>
<body>
    <main class=\"download-card\">
        <h1>Your file is ready to download</h1>
        <a class=\"download-button\" href=\"{safe_url}\" target=\"_blank\" rel=\"noopener noreferrer\" download=\"{safe_download_name}\" aria-label=\"Download {display_name}\">
            <span class="download-icon">{get_file_icon_svg(safe_type)}</span>
            Download file
        </a>
        <div class=\"file-name\">{display_name}</div>
    </main>
    <script>
        function reportHeight() {{
            const h = document.documentElement.scrollHeight;
            parent.postMessage({{ type: 'iframe:height', height: h }}, '*');
        }}
        window.addEventListener('load', reportHeight);
        if (typeof ResizeObserver !== 'undefined') {{
            new ResizeObserver(reportHeight).observe(document.body);
        }} else {{
            window.addEventListener('resize', reportHeight);
        }}
    </script>
</body>
</html>"""

    return HTMLResponse(content=html, headers={"Content-Disposition": "inline", "Content-Type": "text/html"})

# @app.post(
#     "/generate_powerpoint",
#     summary="Generate PowerPoint",
#     description=POWERPOINT_TEMPLATE,
#     operation_id="generate_powerpoint",
# )
async def generate_powerpoint(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = []
):
    """Generates a PowerPoint presentation using a provided Python script. The images_list argument provides a list of 
    image file IDs to be included in the document.
    """
    logger.info("Received request to generate PowerPoint presentation")

    try:
        # headers
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

# @app.post(
#     "/generate_powerpoint_structured_yaml",
#     summary="Generate PowerPoint from YAML",
#     description=POWERPOINT_TEMPLATE_YAML,
#     operation_id="generate_powerpoint_structured_yaml",
# )
async def generate_powerpoint_structured_yaml(
    request: Request,
    file_name: Annotated[
        str,
        Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"]),
    ],
    document_yaml: Annotated[
        str,
        Body(
            ...,
            description="Raw YAML text describing the PowerPoint presentation structure including slides, colors and image references."
        ),
    ],
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

register_powerpoint_tool(
    app=app,
    logger=logger,
    powerpoint_template=POWERPOINT_TEMPLATE,
    enable_structured_yaml_mode=ENABLE_STRUCTURED_YAML_MODE,
    generate_powerpoint=generate_powerpoint,
    generate_powerpoint_structured=generate_powerpoint_structured_yaml,
)

@app.post(
    "/generate_excel",
    summary="Generate Excel",
    description=EXCEL_TEMPLATE,
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
        # headers
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

@app.post(
    "/generate_markdown",
    summary="Generate Markdown",
    description=MARKDOWN_TEMPLATE,
    operation_id="generate_markdown",
)
async def generate_markdown(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
):
    """Generates a Markdown document using a provided Python script."""
    logger.info("Received request to generate Markdown document")
    try:
        request_context = build_request_context(request)
        result = _generate_markdown(
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
        logger.error(f"Error generating Markdown document: {e}")
        return dumps({"error": "An error occurred while generating the Markdown document."}, ensure_ascii=False)

# async def generate_word_structured(
#     request: Request,
#     document_cover: Annotated[Cover, Body(..., description="This argument defines the cover page of the document. Set page_break to True for generating general reports and False for academic papers. Backend is able to center the cover page content automatically so no need to add extra spaces or new lines.")],
#     columns_body: Annotated[int, Body(..., description="This argument defines the number of columns in the document body. Set to 1 for single column or 2 for double column layout for academic papers.")],
#     document_elements: Annotated[List[ElementUnion], Body(..., description="Ordered list of document elements used to build the body. The backend preserves this order as-is. Use top-level objects with a 'type' field: paragraph, header, list, table, image, equation, or page_break.")],
#     file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
# ):
#     """Generates a Word document using provided metadata and body elements."""
#     logger.info("Received request to generate Word document")
#     try:
#         # Check the structure of the document body elements
#         body = DocxBodyElements(document_cover=document_cover, columns_body=columns_body, document_elements=document_elements, file_name=file_name)
#         all_elements = generate_word_template_body_check(body)
#         if isinstance(all_elements, dict) and "error" in all_elements:
#             return dumps(all_elements, ensure_ascii=False)
       
#         # headers
#         request_context = build_request_context(request)
#         result = _generate_word_from_template(
#             document_cover,
#             columns_body,
#             all_elements,
#             file_name,
#             request_context,
#             OWUI_URL,
#             ENABLE_CREATE_KNOWLEDGE,
#             KNOWLEDGE_COLLECTION_NAME
#         )
#         download_html = render_download_button_html(result)
#         return download_html if download_html is not None else result
#     except Exception as e:
#         logger.error(f"Error generating Word document: {e}")
#         return dumps({"error": "An error occurred while generating the Word document."}, ensure_ascii=False)

# @app.post(
#     "/generate_word_structured_yaml",
#     summary="Generate Word from YAML",
#     description=WORD_TEMPLATE_YAML,
#     operation_id="generate_word_structured_yaml",
# )
async def generate_word_structured_yaml(
    request: Request,
    file_name: Annotated[
        str,
        Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"]),
    ],
    document_yaml: Annotated[
        str,
        Body(
            ...,
            description="Raw YAML text describing the cover, columns_body, and body elements for the document."
        ),
    ],
):
    """Generates a Word document from raw YAML text."""
    logger.info("Received request to generate Word document from YAML")
    try:
        body = parse_yaml_to_docx_body(document_yaml, file_name)
        all_elements = generate_word_template_body_check(body)
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
            KNOWLEDGE_COLLECTION_NAME
        )
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except ValueError as e:
        logger.error(f"YAML validation error generating Word document: {e}")
        return dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error generating Word document from YAML: {e}")
        return dumps({"error": "An error occurred while generating the Word document from YAML."}, ensure_ascii=False)

async def generate_word(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = []):
    """
    Generate a Word document using the provided AI-generated Python script. The images_list argument provides a list of 
    image file IDs to be included in the document.
    """
    logger.info("Received request to generate Word document")

    try:
        # headers
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

register_word_tool(
    app=app,
    logger=logger,
    word_template=WORD_TEMPLATE,
    enable_structured_yaml_mode=ENABLE_STRUCTURED_YAML_MODE,
    generate_word_structured=generate_word_structured_yaml,
    generate_word=generate_word,
)

@app.post(
    "/generate_pdf",
    summary="Generate PDF",
    description=PDF_TEMPLATE,
    operation_id="generate_pdf",
)
async def generate_pdf(
    request: Request,
    python_script: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
    images_list: Annotated[List[str], Body(description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])] = []
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
        download_html = render_download_button_html(result)
        return download_html if download_html is not None else result
    except Exception as e:
        logger.error(f"Error generating PDF document: {e}")
        return dumps({"error": "An error occurred while generating the PDF document."}, ensure_ascii=False)

@app.post(
    "/list_docx_elements",
    summary="List DOCX Elements",
    description="Return the DOCX structure with each element's index, style, and text to help identify target sections before adding comments with the review_docx tool.",
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
        # headers
        request_context = build_request_context(request)
        return _full_context_docx(file_id, file_name, request_context, OWUI_URL)
    except Exception as e:
        logger.error(f"Error listing DOCX document elements: {e}")
        return dumps({"error": "An error occurred while listing the DOCX document elements."}, ensure_ascii=False)

@app.post(
    "/review_docx",
    summary="Review DOCX Document",
    description="Review an existing DOCX document and add targeted comments on selected sections to improve spelling, grammar, style, and clarity.",
    operation_id="review_docx",
)
async def review_docx(
    request: Request,
    file_id: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_id"])],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_name"])],
    review_comments: Annotated[List[ReviewComment], Body(..., description=ARGUMENT_DESCRIPTIONS["review_docx"]["review_comments"])]
):
    """Reviews an existing DOCX document and adds comments to specific elements."""
    logger.info("Received request to review DOCX document")
    try:
        # headers
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


def extract_files_from_chat(chat_data):
    files = []
    history = chat_data.get("chat", {}).get("history", {})
    messages = history.get("messages", {})

    for message_id, message in messages.items():
        message_files = message.get("files", [])
        for file_info in message_files:
            files.append({
                # "message_id": message_id,
                "file_id": file_info.get("id"),
                #"file_name": file_info.get("name"),
                # "type": file_info.get("type"),
                # "url": file_info.get("url"),
                # "content_type": file_info.get("content_type")
            })

    return files


@app.get(
        "/fetch_uploaded_chat_file_ids",
        summary="Get Chat Attachments",
        description="Fetch uploaded chat file IDs for context-aware processing: use file IDs for Word review and image IDs for PDF/PPTX/DOCX generation.",
        operation_id="fetch_uploaded_chat_file_ids",
)
async def fetch_uploaded_chat_file_ids(
    request: Request
):
    # headers
    request_context = build_request_context(request)

    attachments = _get_bearer_token(request_context, chat_headers=True)
    if not isinstance(attachments, dict):
        logger.error("Chat headers were not found or could not be parsed from the request.")
        return dumps({"error": "Unable to retrieve chat headers from the request."}, ensure_ascii=False)

    auth_header = attachments.get('authorization') or attachments.get('Authorization')
    chat_id = attachments.get('x-openwebui-chat-id') or attachments.get('X-Open-WebUI-Chat-Id')

    # logger.info(f"Bearer token (if any): {auth_header}")
    # logger.info(f"Chat id: {chat_id}")

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
    except Exception as e:
        logger.exception("=> Exception retrieving chat details")
        return dumps({"error": "An error occurred while retrieving chat attachments."}, ensure_ascii=False)


def main() -> None:
    logger.info(SERVER_BANNER)
    logger.info(f"Starting FastAPI server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host='0.0.0.0', port=PORT)


if __name__ == "__main__":
    main()

    
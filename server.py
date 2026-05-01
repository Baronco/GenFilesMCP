# Native libraries
from json import dumps
from os import getenv
from typing import Annotated, Literal, List, Tuple, Union, Any
from pydantic import Field

# Third-party libraries
from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from html import escape
import uvicorn

# Utilities
from utils.logger import configure_logging, get_logger
configure_logging()
from utils.load_md_templates import load_md_templates
from utils.register_tools import register_word_tool
from utils.argument_descriptions import SERVER_BANNER, MCP_SERVER_NAME, SERVER_VERSION, ARGUMENT_DESCRIPTIONS
from utils.generate_word_template_body_check import generate_word_template_body_check
from utils.pydantic_models_endpoints import DocxBodyElements
from utils.pydantic_models_arguments import Cover, ElementUnion, ReviewComment

# Import tools from the tools directory
from tools.powerpoint_tool import generate_powerpoint as _generate_powerpoint
from tools.excel_tool import generate_excel as _generate_excel
from tools.markdown_tool import generate_markdown as _generate_markdown
from tools.docx_tool import full_context_docx as _full_context_docx, review_docx as _review_docx, generate_word_from_template as _generate_word_from_template
from tools.docx_tool import generate_word as _generate_word
from tools.pdf_tool import generate_pdf as _generate_pdf
# Parameters
ENABLE_WORD_ELEMENT_FILLING = getenv('ENABLE_WORD_ELEMENT_FILLING', 'false').lower() == 'true'
OWUI_URL = getenv('OWUI_URL', 'http://localhost:8080')
PORT = int(getenv('PORT', '8000'))
OWUI_API_KEY = (getenv('OWUI_API_KEY') or '').strip() or None
REVIEWER_AI_ASSISTANT_NAME = getenv('REVIEWER_AI_ASSISTANT_NAME', 'GenFilesMCP')
KNOWLEDGE_COLLECTION_NAME = getenv('KNOWLEDGE_COLLECTION_NAME', 'My Generated Files').strip()
POWERPOINT_TEMPLATE, EXCEL_TEMPLATE, WORD_TEMPLATE, MARKDOWN_TEMPLATE, PDF_TEMPLATE, MCP_INSTRUCTIONS = load_md_templates(ENABLE_WORD_ELEMENT_FILLING)
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
    display_name = escape(f"{file_name}.{file_type}")

    html = f"""<!DOCTYPE html>
<html lang=\"es\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Descargar archivo</title>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f4f6fb;
            color: #111827;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 150px;
        }}
        .download-card {{
            width: min(100%, 420px);
            padding: 24px;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            text-align: center;
        }}
        .download-card h1 {{
            font-size: 1.1rem;
            margin-bottom: 18px;
        }}
        .download-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 14px 22px;
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
            background: #2563eb;
            border: none;
            border-radius: 999px;
            text-decoration: none;
            transition: transform 0.16s ease, background 0.16s ease;
        }}
        .download-button:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}
        .download-button:active {{
            transform: translateY(0);
        }}
        .download-hint {{
            margin-top: 14px;
            color: #6b7280;
            font-size: 0.92rem;
        }}
    </style>
</head>
<body>
    <div class=\"download-card\">
        <h1>Archivo generado correctamente</h1>
        <a class=\"download-button\" href=\"{safe_url}\" target=\"_blank\" rel=\"noopener noreferrer\" download=\"{safe_name}.{safe_type}\">
            Descargar {display_name}
        </a>
        <p class=\"download-hint\">Si el botón no descarga automáticamente, ábrelo en una nueva pestaña.</p>
    </div>
    <script>
        function reportHeight() {{
            const h = document.documentElement.scrollHeight;
            parent.postMessage({{ type: 'iframe:height', height: h }}, '*');
        }}
        window.addEventListener('load', reportHeight);
        new ResizeObserver(reportHeight).observe(document.body);
    </script>
</body>
</html>"""

    return HTMLResponse(content=html, headers={"Content-Disposition": "inline", "Content-Type": "text/html"})

@app.post(
    "/generate_powerpoint",
    summary="Generate PowerPoint",
    description=POWERPOINT_TEMPLATE,
    operation_id="generate_powerpoint",
)
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

async def generate_word_structured(
    request: Request,
    document_cover: Annotated[Cover, Body(..., description="This argument defines the cover page of the document. Set page_break to True for generating general reports and False for academic papers. Backend is able to center the cover page content automatically so no need to add extra spaces or new lines.")],
    columns_body: Annotated[int, Body(..., description="This argument defines the number of columns in the document body. Set to 1 for single column or 2 for double column layout for academic papers.")],
    document_elements: Annotated[List[ElementUnion], Body(..., description="Ordered list of document elements used to build the body. The backend preserves this order as-is. Use top-level objects with a 'type' field: paragraph, header, list, table, image, equation, or page_break.")],
    file_name: Annotated[str, Body(..., description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])],
):
    """Generates a Word document using provided metadata and body elements."""
    logger.info("Received request to generate Word document")
    try:
        # Check the structure of the document body elements
        body = DocxBodyElements(document_cover=document_cover, columns_body=columns_body, document_elements=document_elements, file_name=file_name)
        all_elements = generate_word_template_body_check(body)
        if isinstance(all_elements, dict) and "error" in all_elements:
            return dumps(all_elements, ensure_ascii=False)
       
        # headers
        request_context = build_request_context(request)
        result = _generate_word_from_template(
            document_cover,
            columns_body,
            all_elements,
            file_name,
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
    enable_word_element_filling=ENABLE_WORD_ELEMENT_FILLING,
    generate_word_structured=generate_word_structured,
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


def main() -> None:
    logger.info(SERVER_BANNER)
    logger.info(f"Starting FastAPI server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host='0.0.0.0', port=PORT)


if __name__ == "__main__":
    main()

    
"""FastAPI application factory: assembles all route modules and configures the server."""

from os import getenv

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.config.argument_descriptions import MCP_SERVER_NAME, SERVER_BANNER, SERVER_VERSION
from utils.config.load_md_templates import load_md_templates
from utils.config.logger import configure_logging, get_logger

configure_logging()

ENABLE_STRUCTURED_YAML_MODE = getenv('ENABLE_STRUCTURED_YAML_MODE', 'false').lower() == 'true'
PORT = int(getenv('PORT', '8000'))

(
    POWERPOINT_TEMPLATE,
    EXCEL_TEMPLATE,
    WORD_TEMPLATE,
    MARKDOWN_TEMPLATE,
    PDF_TEMPLATE,
    MCP_INSTRUCTIONS,
    WORD_REVIEW_TEMPLATE,
    FETCH_FILES_TEMPLATE,
) = load_md_templates(ENABLE_STRUCTURED_YAML_MODE)

from api.routes import docx, excel, markdown, pdf, powerpoint, word  # noqa: E402

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

app.include_router(excel.router)
app.include_router(markdown.router)
app.include_router(pdf.router)
app.include_router(docx.router)
app.include_router(word.router)
app.include_router(powerpoint.router)

_ROUTE_DESCRIPTIONS = {
    "generate_excel": EXCEL_TEMPLATE,
    "generate_markdown": MARKDOWN_TEMPLATE,
    "generate_pdf": PDF_TEMPLATE,
    "list_docx_elements": WORD_REVIEW_TEMPLATE,
    "review_docx": WORD_REVIEW_TEMPLATE,
    "fetch_uploaded_chat_file_ids": FETCH_FILES_TEMPLATE,
    "generate_word": WORD_TEMPLATE,
    "generate_word_structured_yaml": WORD_TEMPLATE,
    "generate_powerpoint": POWERPOINT_TEMPLATE,
    "generate_powerpoint_structured_yaml": POWERPOINT_TEMPLATE,
}

for route in app.routes:
    op_id = getattr(route, "operation_id", None)
    if op_id and op_id in _ROUTE_DESCRIPTIONS:
        route.description = _ROUTE_DESCRIPTIONS[op_id]

logger = get_logger(MCP_SERVER_NAME)


def main() -> None:
    """Start the uvicorn server."""
    logger.info(SERVER_BANNER)
    logger.info(f"Starting FastAPI server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host='0.0.0.0', port=PORT)


if __name__ == "__main__":
    main()

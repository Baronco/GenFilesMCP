from utils.config.logger import get_logger

logger = get_logger(__name__)

try:
    ARGUMENT_DESCRIPTIONS = {
        "common_args": {
            "file_name": "Desired name for the generated file without the extension.",
            "python_script": "Complete Python script that generates the PowerPoint presentation using the provided template.",
            "images_list": "List of images file id to be included in the docx file (e.g., ['img1_id', 'img2_id'])."
        },
        "full_context_docx": {
            "file_id": "ID of the existing docx file to analyze (from a previous chat upload).",
            "file_name": "The name of the original docx file"
        },
        "review_docx": {
            "file_id": "ID of the existing docx file to review (from a previous chat upload).",
            "file_name": "The name of the original docx file",
            "review_comments": "List of objects where each object has keys: 'index' (int) and 'comment' (str). Example: [{'index': 0, 'comment': 'Fix typo'}].",
        }
    }

    SERVER_VERSION = "v0.4.0-alpha.5⚡"

    SERVER_BANNER = f"""

    🛠️ Gen Files OpenAPI Server
    ⚙️ Processing & Generating Documents
    🔄 Transforming Ideas into Files
    📝 You can generate '.md', '.docx', '.pptx', '.xlsx' and '.pdf' 🚀 Powered by AI
    🤖 AI-Powered Document Review System (DOCX Only)
    📝 Intelligent Comments & Suggestions Added

    {SERVER_VERSION}
    🌐 https://github.com/Baronco/GenFilesMCP
    """

    MCP_SERVER_NAME = "Gen Files OpenAPI Server"

except Exception:
    logger.error("Error initializing ARGUMENT_DESCRIPTIONS")
    raise

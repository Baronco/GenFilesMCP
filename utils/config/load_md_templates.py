from importlib import resources

from utils.config.logger import get_logger

logger = get_logger(__name__)


import api.shared as _api_shared  # noqa: E402


PLACEHOLDER = "{{SUCCESS_DELIVERY_RULE}}"

ENABLED_SENTENCES: dict[str, str] = {
    "excel.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "markdown.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "pdf.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "word.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "word_template_yaml.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "powerpoint_template_yaml.md": "On success the chat shows a download button \u2014 never invent a download link.",
    "powerpoint.md": "On success the chat shows a download button automatically \u2014 never write or invent a download link.",
    "mcp_instructions.md": "Successful generation shows a **download button** in chat automatically. NEVER write, invent, or repeat a download link.",
    "word_review.md": "On success the chat shows a download button \u2014 never invent a download link.",
}

DISABLED_SENTENCE = (
    "On success the tool returns a structured response that contains a `file_path_download` field \u2014 "
    "that field is already a complete markdown link to the generated file (e.g., "
    "`[Download report.docx](/api/v1/files/<id>/content)`). You MUST expose the `file_path_download` "
    "field to the user **verbatim** in your reply; do not invent, rewrite, shorten, paraphrase, "
    "or otherwise modify the URL."
)


def _apply_success_delivery_rule(filename: str, template: str) -> str:
    """Replace the SUCCESS_DELIVERY_RULE placeholder with the sentence for the current mode.

    When DOWNLOAD_HTML_BUTTON is enabled (default), the file's original sentence is restored
    so the rendered template is byte-identical to the source file. When disabled, a single
    universal sentence is used for every file. Returns the template unchanged when the
    placeholder is absent (safe no-op mid-state during edits).
    """
    if PLACEHOLDER not in template:
        return template
    if _api_shared.DOWNLOAD_HTML_BUTTON:
        sentence = ENABLED_SENTENCES.get(filename, "")
    else:
        sentence = DISABLED_SENTENCE
    return template.replace(PLACEHOLDER, sentence)


def load_md_templates(enable_structured_yaml_mode: bool = False) -> tuple[str, str, str, str, str, str, str, str]:
    """Load Markdown templates used as tool/endpoint descriptions.

    Args:
        enable_structured_yaml_mode: When True, load YAML-based templates for Word and PowerPoint.

    Returns:
        Tuple of (POWERPOINT_TEMPLATE, EXCEL_TEMPLATE, WORD_TEMPLATE, MARKDOWN_TEMPLATE,
        PDF_TEMPLATE, MCP_INSTRUCTIONS, WORD_REVIEW_TEMPLATE, FETCH_FILES_TEMPLATE).
    """
    try:
        with resources.files("src").joinpath("excel.md").open("r", encoding="utf-8") as f:
            EXCEL_TEMPLATE = _apply_success_delivery_rule("excel.md", f.read())

        if enable_structured_yaml_mode:
            with resources.files("src").joinpath("word_template_yaml.md").open("r", encoding="utf-8") as f:
                WORD_TEMPLATE = _apply_success_delivery_rule("word_template_yaml.md", f.read())
        else:
            with resources.files("src").joinpath("word.md").open("r", encoding="utf-8") as f:
                WORD_TEMPLATE = _apply_success_delivery_rule("word.md", f.read())

        if enable_structured_yaml_mode:
            with resources.files("src").joinpath("powerpoint_template_yaml.md").open("r", encoding="utf-8") as f:
                POWERPOINT_TEMPLATE = _apply_success_delivery_rule("powerpoint_template_yaml.md", f.read())
        else:
            with resources.files("src").joinpath("powerpoint.md").open("r", encoding="utf-8") as f:
                POWERPOINT_TEMPLATE = _apply_success_delivery_rule("powerpoint.md", f.read())

        with resources.files("src").joinpath("markdown.md").open("r", encoding="utf-8") as f:
            MARKDOWN_TEMPLATE = _apply_success_delivery_rule("markdown.md", f.read())

        with resources.files("src").joinpath("pdf.md").open("r", encoding="utf-8") as f:
            PDF_TEMPLATE = _apply_success_delivery_rule("pdf.md", f.read())

        with resources.files("src").joinpath("mcp_instructions.md").open("r", encoding="utf-8") as f:
            MCP_INSTRUCTIONS = _apply_success_delivery_rule("mcp_instructions.md", f.read())

        with resources.files("src").joinpath("word_review.md").open("r", encoding="utf-8") as f:
            WORD_REVIEW_TEMPLATE = _apply_success_delivery_rule("word_review.md", f.read())

        with resources.files("src").joinpath("fetch_files.md").open("r", encoding="utf-8") as f:
            FETCH_FILES_TEMPLATE = f.read()

        logger.info("=> Markdown templates loaded successfully.")

        return (
            POWERPOINT_TEMPLATE,
            EXCEL_TEMPLATE,
            WORD_TEMPLATE,
            MARKDOWN_TEMPLATE,
            PDF_TEMPLATE,
            MCP_INSTRUCTIONS,
            WORD_REVIEW_TEMPLATE,
            FETCH_FILES_TEMPLATE
        )

    except Exception as e:
        logger.error("=> Error loading Markdown templates")
        raise e

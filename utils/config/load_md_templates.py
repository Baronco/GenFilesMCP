from importlib import resources

from utils.config.logger import get_logger

logger = get_logger(__name__)


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
            EXCEL_TEMPLATE = f.read()

        if enable_structured_yaml_mode:
            with resources.files("src").joinpath("word_template_yaml.md").open("r", encoding="utf-8") as f:
                WORD_TEMPLATE = f.read()
        else:
            with resources.files("src").joinpath("word.md").open("r", encoding="utf-8") as f:
                WORD_TEMPLATE = f.read()

        if enable_structured_yaml_mode:
            with resources.files("src").joinpath("powerpoint_template_yaml.md").open("r", encoding="utf-8") as f:
                POWERPOINT_TEMPLATE = f.read()
        else:
            with resources.files("src").joinpath("powerpoint.md").open("r", encoding="utf-8") as f:
                POWERPOINT_TEMPLATE = f.read()

        with resources.files("src").joinpath("markdown.md").open("r", encoding="utf-8") as f:
            MARKDOWN_TEMPLATE = f.read()

        with resources.files("src").joinpath("pdf.md").open("r", encoding="utf-8") as f:
            PDF_TEMPLATE = f.read()

        with resources.files("src").joinpath("mcp_instructions.md").open("r", encoding="utf-8") as f:
            MCP_INSTRUCTIONS = f.read()

        with resources.files("src").joinpath("word_review.md").open("r", encoding="utf-8") as f:
            WORD_REVIEW_TEMPLATE = f.read()

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

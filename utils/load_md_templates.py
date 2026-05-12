from utils.logger import get_logger

from importlib import resources

logger = get_logger(__name__)

def load_md_templates(enable_structured_yaml_mode: bool=False) -> tuple[str, str, str, str, str, str, str]:
    """
    Load Markdown templates for PowerPoint, Excel, Word, YAML Word, Markdown, PDF and MCP instructions.

    Returns:
        tuple[str, str, str, str, str, str, str]: A tuple containing the Markdown templates for
                                                   PowerPoint, PowerPoint YAML, Excel, Word, Markdown, PDF and the MCP instructions.
    """

    try:
        # Load Markdown template files using importlib.resources
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

        logger.info("=> Markdown templates loaded successfully.")

        return (
            POWERPOINT_TEMPLATE,
            EXCEL_TEMPLATE,
            WORD_TEMPLATE,
            MARKDOWN_TEMPLATE,
            PDF_TEMPLATE,
            MCP_INSTRUCTIONS
        )
    
    except Exception as e:

        logger.error(f"=> Error loading Markdown templates")
        raise e
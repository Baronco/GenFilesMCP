"""PPTX presentation rendering: YAML parsing, presentation assembly, and generation entry points."""

import re as _re
from io import BytesIO
from json import dumps

import yaml
from pptx import Presentation
from pptx.util import Inches

from tools.pptx.models import THEME_CATALOG, PresentationDefinition
from tools.pptx.slides import BUILDERS
from utils.config.logger import get_logger
from utils.http.authorization import _get_bearer_token
from utils.http.download_file import download_file
from utils.http.get_user_id import get_user_id
from utils.http.knowledge import create_knowledge
from utils.http.upload_file import upload_file

logger = get_logger(__name__)

_DQ_WITH_BACKSLASH_RE = _re.compile(r'"([^"\n]*\\[^"\n]*)"')

_LATEX_HINT_PPTX = (
    " Hint: put latex_lines (and any value with backslashes) in SINGLE quotes so YAML keeps "
    "them literal, e.g. - '$\\lim_{h \\to 0} \\frac{a}{b}$'. In DOUBLE quotes, \\l, \\f, \\t "
    "are read as escape sequences and break the YAML."
)


def _preprocess_yaml_text(raw: str) -> str:
    """Repair common AI-generated YAML mistakes in-place.

    Covers the most frequent errors seen across dozens of real AI outputs:
      - Duplicated keys: `title: "title": "value"` -> `title: "value"`
      - Orphan lines: `-The Math` (dash + word, no colon)
      - `text: "text": "value"` -> `text: "value"`
      - Duplicate keys inside inline dicts: `{x:[1,2], x:x}` -> `{x:[1,2]}`
      - Unquoted bare words in `y: [col1, col2]` lists
      - `file_name` / `OUTPUT` bare words at end of YAML
      - Missing space after dash in list items: `-type:` -> `- type:`
      - Completely empty slides: `- type: content_mixed` followed by `- type:`
    """
    text = raw
    fix_count = [0]

    # 1. Strip BOM and stray control chars (except \t \n \r)
    text = _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. Remove orphan lines like "-The Math" (dash-start, no colon, not a proper list item)
    cleaned = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('-') and ':' not in s and not s.startswith('- ') and not s.startswith('-{') and not s.startswith('-\n'):
            if _re.match(r'^-\w', s):
                fix_count[0] += 1
                continue
        cleaned.append(line)
    text = '\n'.join(cleaned)

    # 3. Fix duplicated keys: `title: "title": "value"` -> `title: "value"`
    text = _re.sub(r'(\w[\w_]*):\s*"\1"\s*:\s*', r'\1: ', text)
    text = _re.sub(r'\{\s*(\w[\w_]*)\s*:\s*"\1"\s*:\s*', r'{\1: ', text)

    # 4. Fix `"text": "text": "..."` -> `"text": "..."`
    text = _re.sub(r'(?:["\x27])?text(?:["\x27])?\s*:\s*["\x27]text["\x27]\s*:\s*', 'text: ', text)

    # 5. Deduplicate last-wins keys inside inline data dicts: {x:[1,2], x:x} -> {x:x}
    def _dedup_inline_dict(m):
        block = m.group(0)
        fix_count[0] += 1
        brace_start = block.index('{')
        brace_end = block.rindex('}')
        inner = block[brace_start + 1:brace_end]
        pairs = _re.split(r',(?=(?:[^\[\]]*\[[^\[\]]*\])*[^\[\]]*$)', inner)
        seen = {}
        for pair in pairs:
            pair = pair.strip()
            if ':' not in pair:
                continue
            k, v = pair.split(':', 1)
            seen[k.strip()] = v.strip()
        deduped = ', '.join(f'{k}: {v}' for k, v in seen.items())
        return block[:brace_start + 1] + deduped + '}'

    text = _re.sub(r'\bdata\s*:\s*\{[^}]+\}', _dedup_inline_dict, text)

    # 6. Fix unquoted bare words in y: [word1, word2] lists
    def _quote_bare_list_items(m):
        prefix = m.group(1)
        inner = m.group(2)
        items = []
        for item in _re.split(r',\s*', inner):
            item = item.strip()
            if (_re.match(r'^[a-zA-Z_]\w*$', item)
                    and item.lower() not in ('true', 'false', 'null', '~', 'yes', 'no', 'on', 'off')):
                items.append(f'"{item}"')
            else:
                items.append(item)
        return f'{prefix}: [{", ".join(items)}]'

    text = _re.sub(r'\b(y|columns)\s*:\s*\[([^\]]+)\]', _quote_bare_list_items, text)

    # 7. Remove trailing bare words that are not valid YAML
    text = _re.sub(r'\n\s*(file_name|OUTPUT|output)\s*(\n|$)', '\n', text, flags=_re.IGNORECASE)

    # 8. Fix missing space after dash in list items: `-type:` -> `- type:`
    text = _re.sub(r'^(\s*)-(\w+)', r'\1- \2', text, flags=_re.MULTILINE)

    # 9. Remove completely empty slides: `- type: content_mixed` followed by `- type: ...`
    text = _re.sub(
        r'(- type: content_mixed\s*\n)(?=- type:)',
        '',
        text,
    )

    if fix_count[0] > 0:
        logger.info("YAML pre-processor applied %d fix(es)", fix_count[0])

    return text


def _strip_control_chars(obj):
    """Recursively remove control characters (except \\t \\n \\r) from all strings in a
    parsed YAML structure, so YAML escape sequences like \\b/\\f can't leak garbage
    control bytes into slide text or titles."""
    if isinstance(obj, str):
        return _re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', obj)
    if isinstance(obj, dict):
        return {k: _strip_control_chars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_control_chars(v) for v in obj]
    return obj


def _coerce_backslash_dq_to_sq(text: str) -> str:
    """Rewrite double-quoted scalars containing a backslash as single-quoted (literal)."""
    return _DQ_WITH_BACKSLASH_RE.sub(lambda m: "'" + m.group(1).replace("'", "''") + "'", text)


def _extract_image_ids_from_yaml(parsed_yaml) -> list[str]:
    image_ids: list[str] = []
    if isinstance(parsed_yaml, dict):
        for key, value in parsed_yaml.items():
            if key == "image_id" and isinstance(value, str):
                image_ids.append(value)
            else:
                image_ids.extend(_extract_image_ids_from_yaml(value))
    elif isinstance(parsed_yaml, list):
        for item in parsed_yaml:
            image_ids.extend(_extract_image_ids_from_yaml(item))
    return image_ids


def create_presentation_from_yaml(
    yaml_text: str,
    output_buffer,
    image_registry: dict = None,
) -> BytesIO:
    """Parse a YAML deck definition, build the presentation, and write it to output_buffer."""
    image_registry = image_registry or {}

    yaml_text = _re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', yaml_text)
    yaml_text = _preprocess_yaml_text(yaml_text)

    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        coerced = _coerce_backslash_dq_to_sq(yaml_text)
        if coerced != yaml_text:
            try:
                raw = yaml.safe_load(coerced)
                logger.info("Recovered PPTX YAML after coercing double-quoted LaTeX to single quotes.")
            except yaml.YAMLError:
                raise ValueError(f"YAML parse error: {exc}.{_LATEX_HINT_PPTX}") from exc
        else:
            raise ValueError(f"YAML parse error: {exc}.{_LATEX_HINT_PPTX}") from exc

    if not isinstance(raw, dict):
        raise ValueError("YAML must be a mapping at the top level.")

    raw = _strip_control_chars(raw)

    if 'global' in raw:
        logger.warning(
            "Ignoring legacy 'global' block - this tool now uses a single 'theme' field "
            "instead of global.accent_color/background_color/font_heading/font_body."
        )
        raw.pop('global', None)

    if 'slides' not in raw:
        for alt in ('slide_list', 'slide', 'pages', 'content'):
            if alt in raw:
                raw['slides'] = raw.pop(alt)
                break

    presentation_def = PresentationDefinition.model_validate(raw)
    theme = THEME_CATALOG[presentation_def.theme]
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)

    _IMPACT_TYPES = {"cover", "section_divider", "stat_highlight"}
    impact_variant = 0
    for i, slide_data in enumerate(presentation_def.slides):
        builder = BUILDERS.get(slide_data.type)
        if not builder:
            logger.warning("Slide %d: type '%s' not implemented, skipping.", i, slide_data.type)
            continue
        variant = 0
        if slide_data.type in _IMPACT_TYPES:
            variant = impact_variant
            impact_variant += 1
        try:
            builder(prs, theme, slide_data, image_registry, variant)
        except Exception as slide_e:
            slide_title = getattr(slide_data, 'title', f'slide {i}')
            logger.warning(
                "Slide %d ('%s') failed: %s. Skipping to keep the rest of the presentation intact.",
                i, slide_title, slide_e,
            )
            continue

    prs.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def generate_powerpoint(python_script, file_name, images_list, request, URL, ENABLE_CREATE_KNOWLEDGE, knowledge_name):
    """Generate a PowerPoint file using an AI-generated Python script.

    Returns:
        dict: Contains 'file_path_download' with a markdown hyperlink for downloading the generated PowerPoint file.
    """
    try:
        images = []

        if len(images_list) > 0:
            logger.info(f"Received {len(images_list)} images for PPTX generation.")

        for idx, image in enumerate(images_list):
            image_file = download_file(URL, _get_bearer_token(request), image)
            if isinstance(image_file, dict) and "error" in image_file:
                return {"error": {"message": f"Error downloading image with ID {image}: {image_file['error']['message']}"}}
            images.append(image_file)

        buffer = BytesIO()
        buffer.name = f'{file_name}.pptx'
        context = {"pptx_buffer": buffer, "images": images}
        try:
            exec(python_script, context)
        except Exception as exec_e:
            return {"error": {"message": f"Error executing script: {str(exec_e)}"}}

        buffer.seek(0)

        try:
            bearer_token = _get_bearer_token(request)
            logger.info("=> Received authorization header!")
        except Exception:
            logger.error("=> Error retrieving authorization header")

        user_id = get_user_id(URL, bearer_token)
        if not user_id:
            logger.error("=> Error obtaining user id from token")
            return dumps({"error": {"message": "Error obtaining user id from token"}}, indent=4, ensure_ascii=False)

        response, request_data = upload_file(
            url=URL,
            token=bearer_token,
            file_data=buffer,
            filename=file_name,
            file_type="pptx"
        )

        if "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE:
            create_knowledge_status = create_knowledge(
                url=URL,
                token=bearer_token,
                file_id=request_data['id'],
                user_id=user_id,
                knowledge_name=knowledge_name
            )
            if create_knowledge_status:
                logger.info("=> Knowledge base updated successfully.")
            else:
                logger.error("=> Error creating or updating knowledge base")
        elif "error" in response:
            logger.error("=> Error uploading the file.")
        else:
            logger.info("=> Skipping knowledge creation because ENABLE_CREATE_KNOWLEDGE is false")

        return response

    except Exception as e:
        logger.error("=> An unknown error occurred during .PPTX document generation.")
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            },
            indent=4,
            ensure_ascii=False
        )


def generate_powerpoint_structured_yaml(
    document_yaml,
    file_name,
    request,
    URL,
    ENABLE_CREATE_KNOWLEDGE,
    knowledge_name,
):
    """Generate a PPTX from a YAML deck definition and upload it; returns the upload response dict."""
    try:
        try:
            parsed_yaml = yaml.safe_load(document_yaml)
        except yaml.YAMLError as exc:
            return {"error": {"message": f"YAML parse error: {exc}"}}

        image_ids = list(dict.fromkeys(_extract_image_ids_from_yaml(parsed_yaml)))
        images = []

        if image_ids:
            logger.info(f"Received {len(image_ids)} image references for PPTX YAML generation.")

        for image_id in image_ids:
            image_file = download_file(URL, _get_bearer_token(request), image_id)
            if isinstance(image_file, dict) and "error" in image_file:
                return {"error": {"message": f"Error downloading image with ID {image_id}: {image_file['error']['message']}"}}
            image_file.seek(0)
            images.append(image_file)

        image_registry = {image_id: image_file for image_id, image_file in zip(image_ids, images)}
        buffer = BytesIO()
        buffer.name = f"{file_name}.pptx"

        try:
            create_presentation_from_yaml(document_yaml, buffer, image_registry)
        except Exception as exec_e:
            error_msg = str(exec_e)
            hints = []
            if "YAML parse error" in error_msg:
                hints.append(
                    "Suggestion: Check for duplicated keys like `title: \"title\": \"value\"` "
                    "or unquoted bare words in lists like `y: [col1, col2]`. "
                    "Ensure every list item starts with `- ` (dash + space)."
                )
            elif "content_mixed" in error_msg and "image_id" in error_msg:
                hints.append(
                    "Suggestion: A content_mixed slide has both image_id AND chart/table. "
                    "Use ONLY ONE visual element per slide."
                )
            elif "charts require" in error_msg:
                hints.append(
                    "Suggestion: 'comparison'/'part_of_whole' charts need 'categories' + 'values' "
                    "(or 'categories' + 'series'); 'trend' charts need 'x' + 'y'; "
                    "'distribution' charts need 'values'. For multiple bars/lines use 'series' "
                    "(a list of {name, values}); an optional 'chart_type' picks a specific shape."
                )
            if hints:
                error_msg = error_msg + "\n\n" + "\n".join(hints)
            return {"error": {"message": f"Error generating PowerPoint from YAML: {error_msg}"}}

        buffer.seek(0)

        try:
            bearer_token = _get_bearer_token(request)
            if bearer_token:
                logger.info("=> Received authorization header!")
            else:
                logger.warning("=> Authorization header is missing.")
        except Exception:
            logger.exception("=> Error retrieving authorization header")
            bearer_token = None

        user_id = None
        if bearer_token:
            user_id = get_user_id(URL, bearer_token)
            if not user_id:
                logger.warning("=> Could not obtain user id from token; continuing without knowledge creation.")

        response, request_data = upload_file(
            url=URL,
            token=bearer_token,
            file_data=buffer,
            filename=file_name,
            file_type="pptx"
        )

        if "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE and user_id:
            create_knowledge_status = create_knowledge(
                url=URL,
                token=bearer_token,
                file_id=request_data['id'],
                user_id=user_id,
                knowledge_name=knowledge_name
            )
            if create_knowledge_status:
                logger.info("=> Knowledge base updated successfully.")
            else:
                logger.error("=> Error creating or updating knowledge base")
        elif "file_path_download" in response and ENABLE_CREATE_KNOWLEDGE and not user_id:
            logger.warning("=> Skipping knowledge creation because user_id is unavailable.")
        elif "error" in response:
            logger.error("=> Error uploading the file.")
        else:
            logger.info("=> Skipping knowledge creation because ENABLE_CREATE_KNOWLEDGE is false")

        return response
    except Exception as e:
        logger.error("=> An unknown error occurred during .PPTX document generation from YAML.")
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            },
            indent=4,
            ensure_ascii=False
        )

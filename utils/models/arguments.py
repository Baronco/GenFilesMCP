import json
from typing import Annotated, List, Literal, Optional, Union, get_args, get_origin

from pydantic import BaseModel, Field

from utils.config.logger import get_logger

logger = get_logger(__name__)

# --- Models for review comments and document elements ---
class ReviewComment(BaseModel):
    index: int
    comment: str

class ImagesList(BaseModel):
    images: str

# --- Simplified structured DOCX document element models ---
class ElemHeader(BaseModel):
    type: Literal["header"] = Field(..., description="Heading element type.")
    text: str = Field(..., description="Heading text. No Markdown.")
    level: Literal[1, 2, 3, 4, 5, 6] = Field(..., description="1=main section, 6=minor subsection.")

class ElemParagraph(BaseModel):
    type: Literal["paragraph"] = Field(..., description="Paragraph element type.")
    text: str = Field(..., description="Body text. Supports **bold** and *italic*.")

class ElemList(BaseModel):
    type: Literal["list"] = Field(..., description="List element type.")
    style: Literal["bullet", "numbered"] = Field(..., description="List style. Use 'bullet' or 'numbered'.")
    items: List[str] = Field(..., description="Each string is one list item. No Markdown inside items.")

class ElemTable(BaseModel):
    type: Literal["table"] = Field(..., description="Table element type.")
    headers: List[str] = Field(..., description="Column headers in display order.")
    rows: List[List[str]] = Field(..., description="Each row must match the header count.")
    caption: Optional[str] = Field(default=None, description="Optional caption for the table.")

class ElemImage(BaseModel):
    type: Literal["image"] = Field(..., description="Image element type.")
    id: str = Field(..., description="Exact file ID from the uploaded image. Do not modify.")
    caption: Optional[str] = Field(default=None, description="Optional caption for the image.")

class ElemEquation(BaseModel):
    type: Literal["equation"] = Field(..., description="LaTeX equation element type.")
    latex: str = Field(..., description="LaTeX expression, for example: E = mc^{2}")
    caption: Optional[str] = Field(default=None, description="Optional caption for the equation.")

class ElemPageBreak(BaseModel):
    type: Literal["page_break"] = Field(..., description="Page break element type.")

# --- Models for docx document structure ---
class Cover(BaseModel):
    title: str = Field(..., description="Cover title. Use a short, specific title.")
    subtitle: str = Field(..., description="Cover subtitle. Use only if it adds context.")
    description: str = Field(..., description="One concise sentence describing the purpose of the document.")
    author: str = Field(..., description="Author name as it should appear on the cover.")
    month: str = Field(..., description="Publication month in plain text, for example: 'January'.")
    year: str = Field(..., description="Publication year in 4 digits, for example: '2024'.")
    page_break: bool = Field(..., description="Set true to start body content on a new page after the cover; false to continue immediately.")

class ParagraphListItem(BaseModel):
    list_style: Literal['List Number', 'List Bullet'] = Field(..., description="When adding a list to a docx document, choose either 'List Number' or 'List Bullet' based on the desired formatting style.")
    items: List[str] = Field(..., description="List entries must include one or more non-empty strings, with each string representing a separate item. This type does not support Markdown formatting for bold or italic text. Do not use this type for equations; use the type 'Equation' instead to ensure proper formatting.")

class Table(BaseModel):
    table_headers: List[str] = Field(..., description="Column headers in display order.")
    table_rows: List[List[str]] = Field(..., description="Table rows. Each row must match the number of headers.")
    caption: str = Field(..., description="Caption for the table. Captions should be brief and concise. For example: 'Table 1: Summary of experimental results.'")

class Image(BaseModel):
    id: str = Field(..., description="Unique file ID of the image. Use the `chat_context` tool to retrieve the IDs of images uploaded in the conversation chat. This allows the backend to download the image and include it in the document. Do not modify the ID format, as it must remain a unique string that identifies the uploaded image.")
    caption: str = Field(..., description="Caption for the image. Captions should be brief and concise. For example: 'Figure 1: Diagram of the experimental setup.'")

class Equation(BaseModel):
    latex: str = Field(..., description="Required LaTeX expression, for example: E = mc^{2}")
    caption: str = Field(..., description="Caption for the equation. Captions should be brief and concise. For example: 'Equation 1: Einstein's mass-energy equivalence.'")

class ParagraphHeader(BaseModel):
    text: str = Field(..., description="Heading text in plain language. Markdown formatting is not allowed")
    level: Literal[1,2,3,4,5,6] = Field(..., description="Heading level from 1 (main section) to 6 (minor subsection).")

class ParagraphBody(BaseModel):
    text: str = Field(
        ...,
        description=(
            "Paragraph content. Markdown emphasis is allowed: **bold** and *italic*. "
            "Line breaks can be created by adding them directly in the text. "
            "For consecutive paragraphs, use multiple 'ParagraphBody' elements in the element list. "
            "Do not include titles in this field; use the type 'ParagraphHeader' for titles. "
            "If you need to create lists, use the type 'ParagraphListItem'. "
            "Similarly, do not use 'ParagraphBody' for equations; use the type 'Equation' instead."
        )
    )

class ParagraphBodyElement(BaseModel):
    type: Literal["ParagraphBody"] = Field(..., description="Element type for paragraph body.")
    text: str = Field(..., description="Paragraph content. Markdown emphasis is allowed: **bold** and *italic*.")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")

class ParagraphHeaderElement(BaseModel):
    type: Literal["ParagraphHeader"] = Field(..., description="Element type for a heading.")
    text: str = Field(..., description="Heading text in plain language. Markdown formatting is not allowed.")
    level: Literal[1,2,3,4,5,6] = Field(..., description="Heading level from 1 (main section) to 6 (minor subsection).")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")

class ParagraphListItemElement(BaseModel):
    type: Literal["ParagraphListItem"] = Field(..., description="Element type for a list.")
    list_style: Literal['List Number', 'List Bullet'] = Field(..., description="Choose 'List Number' or 'List Bullet'.")
    items: List[str] = Field(..., description="List entries must include one or more non-empty strings.")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")

class TableElement(BaseModel):
    type: Literal["Table"] = Field(..., description="Element type for a table.")
    table_headers: List[str] = Field(..., description="Column headers in display order.")
    table_rows: List[List[str]] = Field(..., description="Table rows. Each row must match the number of headers.")
    caption: Optional[str] = Field(default="", description="Optional caption for the table.")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")

class ImageElement(BaseModel):
    type: Literal["Image"] = Field(..., description="Element type for an image.")
    id: str = Field(..., description="Unique file ID of the image.")
    caption: Optional[str] = Field(default="", description="Optional caption for the image.")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")

class EquationElement(BaseModel):
    type: Literal["Equation"] = Field(..., description="Element type for an equation.")
    latex: str = Field(..., description="Required LaTeX expression, for example: E = mc^{2}")
    caption: Optional[str] = Field(default="", description="Optional caption for the equation.")
    index_element: Optional[int] = Field(default=None, description="Optional ordering index. If omitted, list order is preserved.")


def _fields_summary(model: type[BaseModel]) -> str:
    """Generate a compact field summary string for a Pydantic model, used in Field descriptions."""
    required_fields = [name for name, info in model.model_fields.items() if info.is_required()]
    required_text = ", ".join(required_fields) if required_fields else "none"

    field_details = []
    json_example = {}
    for name, info in model.model_fields.items():
        description = info.description or "No description provided."
        annotation = info.annotation
        origin = get_origin(annotation)

        literal_options = get_args(annotation) if origin is Literal else ()
        if literal_options:
            options_text = " | ".join([f"'{opt}'" for opt in literal_options])
            field_details.append(f"{name}: {description} Allowed values: {options_text}.")
            json_example[name] = literal_options[0]
        elif origin is list:
            json_example[name] = ["..."]
            field_details.append(f"{name}: {description}")
        elif annotation in (int, float):
            json_example[name] = 1
            field_details.append(f"{name}: {description}")
        elif annotation is bool:
            json_example[name] = True
            field_details.append(f"{name}: {description}")
        else:
            json_example[name] = "..."
            field_details.append(f"{name}: {description}")

    details_text = " | ".join(field_details) if field_details else "No field details."
    example_text = json.dumps(json_example, ensure_ascii=False)
    return (
        f"All keys inside this object are required. "
        f"Required fields: [{required_text}]. "
        f"Field details: {details_text}. "
        f"JSON shape example: {example_text}."
    )


elements_lit = Literal[
    "ParagraphBody",
    "ParagraphHeader",
    "ParagraphListItem",
    "Table",
    "Image",
    "Equation"
]

class DocumentElement(BaseModel):
    type: elements_lit = Field(..., description="Specify exactly one of the following types: ParagraphBody, ParagraphHeader, ParagraphListItem, Table, Image, or Equation. Do not alter these literals, as it will cause backend failures.")
    paragraph: Optional[ParagraphBody] = Field(default=None, description=f"Use only when type='ParagraphBody'. Omit for any other type. {_fields_summary(ParagraphBody)}")
    header: Optional[ParagraphHeader] = Field(default=None, description=f"Use only when type='ParagraphHeader'. Omit for any other type. {_fields_summary(ParagraphHeader)}")
    list_item: Optional[ParagraphListItem] = Field(default=None, description=f"Use only when type='ParagraphListItem'. Omit for any other type. {_fields_summary(ParagraphListItem)}")
    table: Optional[Table] = Field(default=None, description=f"Use only when type='Table'. Omit for any other type. {_fields_summary(Table)}")
    image: Optional[Image] = Field(default=None, description=f"Use only when type='Image'. Omit for any other type. {_fields_summary(Image)}")
    equation: Optional[Equation] = Field(default=None, description=f"Use only when type='Equation'. Omit for any other type. {_fields_summary(Equation)}")

DocElement = Annotated[
    Union[
        ElemHeader,
        ElemParagraph,
        ElemList,
        ElemTable,
        ElemImage,
        ElemEquation,
        ElemPageBreak,
    ],
    Field(discriminator="type")
]

ElementUnion = DocElement

logger.info("=> Pydantic argument models loaded successfully.")

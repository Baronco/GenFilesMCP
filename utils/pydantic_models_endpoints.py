from pydantic import BaseModel, Field
from typing import List, Union
from utils.argument_descriptions import ARGUMENT_DESCRIPTIONS
from utils.logger import get_logger
from utils.pydantic_models_arguments import (
    Cover,
    ElementUnion,
    ReviewComment,
)

logger = get_logger(__name__)

# --- Request Models for API Endpoints ---
class GeneratePowerPointRequest(BaseModel):
    python_script: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])
    images_list: List[str] = Field(default_factory=list, description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])

class GenerateExcelRequest(BaseModel):
    python_script: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])

class GenerateMarkdownRequest(BaseModel):
    python_script: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])

class GeneratePdfRequest(BaseModel):
    python_script: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["python_script"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])
    images_list: List[str] = Field(default_factory=list, description=ARGUMENT_DESCRIPTIONS["common_args"]["images_list"])
 
class DocxBodyElements(BaseModel):
    document_cover: Cover = Field(description="This argument defines the cover page of the document. Set page_break to True for generating general reports and False for academic papers. Backend is able to center the cover page content automatically so no need to add extra spaces or new lines.")
    columns_body: int = Field(description="This argument defines the number of columns in the document body. Set to 1 for single column or 2 for double column layout for academic papers.")
    document_elements: List[Union[ElementUnion, dict]] = Field(
        description=(
            "Ordered list of document elements used to build the body. The backend preserves this order as-is. "
            "Use top-level objects with a 'type' field: paragraph, header, list, table, image, equation, or page_break. "
            "Legacy nested dicts are also accepted."
        )
    )
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["common_args"]["file_name"])

class FullContextDocxRequest(BaseModel):
    file_id: str = Field(description=ARGUMENT_DESCRIPTIONS["full_context_docx"]["file_id"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["full_context_docx"]["file_name"])

class ReviewDocxRequest(BaseModel):
    file_id: str = Field(description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_id"])
    review_comments: List[ReviewComment] = Field(description=ARGUMENT_DESCRIPTIONS["review_docx"]["review_comments"])
    file_name: str = Field(description=ARGUMENT_DESCRIPTIONS["review_docx"]["file_name"])

logger.info("=> Pydantic endpoint models loaded successfully.")

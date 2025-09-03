# Native libraries
from json import dumps
from os import getenv, makedirs
from os.path import exists
from shutil import rmtree
from typing import Annotated, Literal
from enum import Enum
from uuid import uuid4
from pathlib import Path

# Third-party libraries
from pydantic import Field
from requests import post
from mcp.server.fastmcp import FastMCP

# from dotenv import load_dotenv
# load_dotenv()

URL = getenv('OWUI_URL')
TOKEN = getenv('JWT_SECRET')
PORT = int(getenv('PORT'))

# helpers uploading files
def upload_file(url: str, token: str, file_path: str, filename:str, file_type:str) -> dict:
    """ 
    Upload a file to the specified URL with the provided token.
    Args:
        url (str): The URL to which the file will be uploaded.
        token (str): The authorization token for the request.
        file_path (str): The path to the file to be uploaded.
    Returns:
        dict: A dict containing the result of the upload operation.
    """
    # Ensure the URL ends with '/api/v1/files/'
    url = f'{url}/api/v1/files/'

    # Prepare headers and files for the request
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    # Open the file and send the POST request
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = post(url, headers=headers, files=files)


    if response.status_code != 200:
       return dumps({"error":{"message": f'Error uploading file: {response.status_code}'}})
    else:
        return dumps(
            {
            "file_path_download": f"[Download {filename}.{file_type}](/api/v1/files/{response.json()['id']}/content)"
            },
            indent=4,
            ensure_ascii=False
        )

mcp = FastMCP(
    name="GenFilesMCP",
    instructions=
        "Generates PowerPoint, Excel, Words or Markdown files from user requests and chat context.",
    port=PORT,
    host="0.0.0.0"
)

@mcp.tool(
    name='file_template_script',
    title="Python templates.",
    description="Python script templates to generate PowerPoint, Excel, Word or Markdown files"
)
def template(
    file_type: Annotated[
        str,
        Field(
            description="Supported file types: pptx (PowerPoint), xlsx (Excel), docx (Word), md (Markdown).",
            default="md",
            json_schema_extra={"FileType": ["pptx", "xlsx", "docx", "md"]}
        )
    ]
) -> dict:
    """
    Return a Python script template to generate PowerPoint, Excel, Word or Markdown files
    """
    base = Path(__file__).parent / "template"

    if file_type == "pptx":
        with (base / "powerpoint.md").open("r", encoding="utf-8") as f:
            template_text = f.read()
    elif file_type == "xlsx":
        with (base / "excel.md").open("r", encoding="utf-8") as f:
            template_text = f.read()
    elif file_type == "docx":
        with (base / "word.md").open("r", encoding="utf-8") as f:
            template_text = f.read()
    elif file_type == "md":
        with (base / "markdown.md").open("r", encoding="utf-8") as f:
            template_text = f.read()
    else:
        return dumps(
            {
                "error": {
                    "message": "This MCP tool only supports pptx, xlsx, docx and md fies"
                }
            }, 
            indent=4, 
            ensure_ascii=False
        )

    return dumps(
        {
            "file_type": file_type, 
            "python_template": template_text
        }, 
        indent=4, 
        ensure_ascii=False
    )

@mcp.tool(
    name="file_generation",
    title="Files generation using.",
    description="Executes a Python script, built using the provided template, to generate PowerPoint, Excel, Word or Markdown files"
)
def files_generation(
    python_script: Annotated[
        str, 
        Field(description="Python script that generates the PowerPoint, Excel, Word or Markdown using the provided template.")
    ],
    file_name: Annotated[
        str, 
        Field(description="Desired name for the generated PowerPoint, Excel, Word or Markdown file without the extension.")
    ],
    file_type: Annotated[
        str,
        Field(
            description="File type for generated files pptx (PowerPoint), xlsx (Excel), docx (Word), md (Markdown).",
            default="md",
            json_schema_extra={"FileType": ["pptx", "xlsx", "docx", "md"]}
        )
    ]
) -> dict:
    """
    Generate a PowerPoint, Excel, Word or Markdown file using a Python script.

    Returns:
        dict: A message indicating the success of the PowerPoint creation.
    """
    # user folder
    if not exists('/app/temp'):
        makedirs('/app/temp')
    try:
        # Generate a unique filename for the PowerPoint file
        file_path = f'/app/temp/{file_name}_{uuid4()}.{file_type}'
        context = {f"{file_type}_path": file_path}
        exec(python_script, context )

        # Upload the generated PowerPoint file
        response = upload_file(
            url=URL, 
            token=TOKEN, 
            file_path=file_path,
            filename=file_name,
            file_type=file_type
        )

        # remove the temporary file after upload
        rmtree('/app/temp', ignore_errors=True)
        
        return response 
    
    except Exception as e:
        return dumps(
            {
                "error": {
                    "message": str(e)
                }
            }, 
            indent=4, 
            ensure_ascii=False
        )

# Initialize and run the server
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )


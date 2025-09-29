
# GenFilesMCP (MVP) 🧩

GenFilesMCP is a minimal viable product (MVP) MCP that generates PowerPoint, Excel, Word, or Markdown files from user requests and chat context. This MCP executes Python templates to produce files and uploads them to an Open Web UI (OWUI) endpoint. Use with caution: the MCP executes code and should be run in a controlled environment (recommended: Docker).

## 🚀 What it does

- Receives generation requests via a FastMCP server.
- Uses Python templates to create files in one of these formats: pptx, xlsx, docx, md.
- Saves the generated file to a temporary path and uploads it to an OWUI API endpoint (/api/v1/files/).
- Additionally, it supports analyzing and reviewing existing Word documents (docx) by extracting their structure and adding comments to specific elements for corrections, grammar suggestions, or idea enhancements.

## ⚠️ Current status

This is an MVP. It works for generating and uploading files but still needs improvements in security, validation, template sanitization, logging, and error handling. For now, run it locally or inside Docker and avoid exposing it on public networks.

## 🐳 Recommended: Run with Docker

Because the MCP executes Python code based on templates, running inside Docker reduces risk to your host system.

Prerequisites:
- Docker installed
- Clone this repository

Build the Docker image:

```bash
docker build -t gen_files_mcp .
```

Run the container (replace YOUR_PORT and YOUR_JWT_SECRET):

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT -e OWUI_URL="http://host.docker.internal:3000" -e JWT_SECRET="YOUR_JWT_SECRET" -e PORT=YOUR_PORT --name gen_files_mcp gen_files_mcp
```

Note:
- OWUI_URL => The local URL of your Open Web UI instance (e.g. http://host.docker.internal:3000)

## 🔌 MCP configuration (MCPO)

Your MCPO (MCP orchestration) config must include an entry for this MCP, for example:

```json
{
  "mcpServers": {
    "GenFilesMCP": {
      "type": "streamable_http",
      "url": "http://host.docker.internal:YOUR_PORT/mcp/"
    }
  }
}
```

## 🔐 OWUI Administrator Settings

- The JWT token used by the MCP can be found in OWUI Admin settings under the Account module.

## 🧪 Usage Notes

- The MCP expects these environment variables:
  - OWUI_URL: URL of the OWUI instance
  - JWT_SECRET: JWT token used to upload files
  - PORT: Port where the MCP will listen

- The MCP uses temporary files under `/app/temp` and uploads them using the OWUI files API.

## ✅ Limitations & Next steps

- Add input sanitization and template validation to prevent arbitrary code execution.
- Implement RBAC, authentication for MCP endpoints, and rate limiting.
- Improve logging and error reporting.
- Provide a secure template sandbox or a pre-approved template store.

## 📝 Reviewing Word Documents (Experimental 🧪)

### Prerequisites
- Upload a docx file to your Open Web UI chat context.
- Create a custom tool in Open Web UI to retrieve the file ID and name of uploaded docx files. Go to **Workspace > Tools > (+) Create** and add the following code:

```python
import os
import requests
from datetime import datetime
from pydantic import BaseModel, Field


class Tools:
    def __init__(self):
        pass

    # Add your custom tools using pure Python code here, make sure to add type hints and descriptions

    def get_files_metadata(self, __files__: dict = {}) -> dict:
        """
        Get files metadata
        """
        # id and name of current files
        chat_current_files = {"files": []}

        if __files__ is not None:
            for f in __files__:
                chat_current_files["files"].append({"id": f["id"], "name": f["name"]})
            return chat_current_files
        else:
            message = {
                "message": "There are no documents uploaded in the current chat."
            }
            return message

```

You can create the tool from Workspace > Tools > (+) Create, and paste the code above. 

<div style="text-align: center;">

  ![server](img/filestool.png)

</div>

# System prompt for FileGenAgent

You can find the system prompt for this MCP in the file `example/systemprompt.md`. It is recommended to copy it to your OWUI instance and create a custom agent called **FileGenAgent** with this system prompt. This way, you can easily use the MCP in your chats. Tested with GPT-5 Thinking mini.

## Example generating a docx file

<div style="text-align: center;">

  ![server](img/example2.png)

</div>

> You can find the prompt and result in the example folder `History_of_Neural_Nets_Summary_69d1751b-577b-4329-beca-ac16db7acdbd.docx`.

> This file was generated using the GenFiles MCP server and GPT5-mini

## Example reviewing a docx file with comments

<div style="text-align: center;">

  ![server](img/reviewer1.png)

</div>

<div style="text-align: center;">

  ![server](img/reviewer2.png)

</div>


<div style="text-align: center;">

  ![server](img/reviewer3.png)

</div>

The user uploaded a file called `History_of_Neural_Nets_Summary.docx` and asked the agent to review it and add comments for corrections, grammar suggestions, and idea enhancements. The agent first called the custom tool `get_files_metadata` to get the file ID and name of the uploaded docx file. Then, it called the MCP to get the full context of the docx file using the `full_context_docx` function. Finally, it called the `review_docx` function to add comments to specific elements in the docx file:


<div style="text-align: center;">

  ![server](img/docxcomments.png)

</div>

> You can find the result in the example folder `History_of_Neural_Nets_Summary_reviewed_a35adcc5-e338-47c6-a0b0-2c21602b0777.docx`.

> This file was generated using the GenFiles MCP server and GPT5-mini

> The review functionality conserves the original formatting of the document while adding comments to specified elements.


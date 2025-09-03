
# GenFilesMCP (MVP) 🧩

GenFilesMCP is a minimal viable product (MVP) MCP that generates PowerPoint, Excel, Word, or Markdown files from user requests and chat context. This MCP executes Python templates to produce files and uploads them to an Open Web UI (OWUI) endpoint. Use with caution: the MCP executes code and should be run in a controlled environment (recommended: Docker).

## 🚀 What it does

- Receives generation requests via a FastMCP server.
- Uses Python templates to create files in one of these formats: pptx, xlsx, docx, md.
- Saves the generated file to a temporary path and uploads it to an OWUI API endpoint (/api/v1/files/).

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

- In the OWUI Admin settings, under General, enable "API Key Endpoint Restrictions" and add the path `/api/v1/files`.
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

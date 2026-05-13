## Table of Contents

- [Deployment Prerequisites](#deployment-prerequisites)
- [Installation](#installation)
  - [Option 1: Pre-built Docker Image (Recommended)](#option-1-pre-built-docker-image-recommended)
  - [Option 2: Building from Source](#option-2-building-from-source)
  - [Option 3: Docker Compose](#option-3-docker-compose)
- [Open WebUI Requirements](#open-webui-requirements)
  - [Environment Variables (Open WebUI side)](#environment-variables-open-webui-side)
  - [GenFiles Environment Variables](#genfiles-environment-variables)
  - [Knowledge Base and Permissions](#knowledge-base-and-permissions)
  - [GenFiles Document Upload Settings](#genfiles-document-upload-settings)
- [OpenAPI Tool Configuration in Open WebUI](#openapi-tool-configuration-in-open-webui)
- [Document Generation Setup](#document-generation-setup)
  - [System Prompt for your AI Assistant](#system-prompt-for-your-ai-assistant)

## Deployment Prerequisites

- **Docker** installed on your system
- **Open WebUI >= 0.9.0**

GenFiles runs as a standalone HTTP OpenAPI service. Open WebUI registers it as an `OpenApi` external tool and forwards the active user's bearer token to the server so documents are generated and uploaded on behalf of the correct user.

## Installation

### Option 1: Pre-built Docker Image (Recommended)

Pull the pre-built Docker image from GitHub Container Registry:

```bash
docker pull ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.4
```

Run the container:

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.4
```

One-line command (copy/paste):

```bash
docker run -d --restart unless-stopped -p 8016:8016 -e OWUI_URL="http://host.docker.internal:3000" -e PORT=8016 -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" -e ENABLE_CREATE_KNOWLEDGE=false --name gen_files_mcp ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.4
```

Or use the `:latest` tag:

```bash
docker run -d --restart unless-stopped -p 8016:8016 -e OWUI_URL="http://host.docker.internal:3000" -e PORT=8016 -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" -e ENABLE_CREATE_KNOWLEDGE=false --name gen_files_mcp ghcr.io/baronco/genfiles-openapi:latest
```

These minimal examples keep knowledge persistence disabled. Add `KNOWLEDGE_COLLECTION_NAME` only if you change `ENABLE_CREATE_KNOWLEDGE` to `true`.

### Option 2: Building from Source

1. Clone the repository:

```bash
git clone https://github.com/Baronco/GenFilesMCP.git
cd GenFilesMCP
```

2. Build the Docker image:

```bash
docker build -t gen_files_mcp .
```

3. Run the container:

```bash
docker run -d --restart unless-stopped \
  -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  gen_files_mcp
```

### Option 3: Docker Compose

Using the published image:

```yaml
services:
  genfiles:
    image: ghcr.io/baronco/genfiles-openapi:latest
    container_name: gen_files_mcp
    environment:
      - REVIEWER_AI_ASSISTANT_NAME=GenFilesMCP
      - ENABLE_CREATE_KNOWLEDGE=false
      - OWUI_URL=http://open-webui:8080
      - PORT=8016
    ports:
      - "8016:8016"
```

Or build from local source:

```yaml
services:
  genfiles:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: gen_files_mcp
    environment:
      - REVIEWER_AI_ASSISTANT_NAME=GenFilesMCP
      - ENABLE_CREATE_KNOWLEDGE=false
      - OWUI_URL=http://open-webui:8080
      - PORT=8016
    ports:
      - "8016:8016"
```

Run:

```bash
docker compose up -d
```

## Open WebUI Requirements

### Environment Variables (Open WebUI side)

The following variable must be set in your **Open WebUI** environment (not in the GenFiles container):

| Variable | Value | Description |
|----------|-------|-------------|
| `ENABLE_FORWARD_USER_INFO_HEADERS` | `True` | Tells Open WebUI to forward the active session's bearer token to external tools. **Required** so GenFiles can upload and download files on behalf of the correct user. |

> Without `ENABLE_FORWARD_USER_INFO_HEADERS=True`, GenFiles cannot authenticate as the calling user and document uploads will fail.

Additionally, set `JWT Expiration` to a finite duration such as `4h` in Open WebUI settings. Do not leave it at `-1`.

### GenFiles Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OWUI_URL` | URL of your Open WebUI instance | `http://host.docker.internal:3000` |
| `PORT` | Port where GenFiles will listen | `8016` |
| `KNOWLEDGE_COLLECTION_NAME` | Name of the Open WebUI knowledge collection used when `ENABLE_CREATE_KNOWLEDGE=true` | `My Generated Files` |
| `REVIEWER_AI_ASSISTANT_NAME` | Author name used inside Word comments created by `review_docx` | `GenFilesMCP` |
| `ENABLE_CREATE_KNOWLEDGE` | Whether generated or reviewed files are added to Open WebUI knowledge collections | `false` |
| `ENABLE_STRUCTURED_YAML_MODE` | Enables YAML-based structured generation for Word and PowerPoint (preferred mode) | `true` |

### Knowledge Base and Permissions

- **Permission Requirement**: Administrators must enable `Workspace Permissions -> Knowledge Access` for the users who should access knowledge collections, either through `Default permissions` or through the relevant Open WebUI group.

<p align="center">
  <img src="../img/permissions.png" alt="Knowledge Access Permission" />
</p>

- If `ENABLE_CREATE_KNOWLEDGE=true`, GenFiles creates or updates a per-user knowledge collection named `KNOWLEDGE_COLLECTION_NAME` for the active user session. Manual collection creation is not required.
- If `ENABLE_CREATE_KNOWLEDGE=false`, `KNOWLEDGE_COLLECTION_NAME` is ignored and no knowledge collection is created.
- Users who should access knowledge collections must have `Workspace Permissions -> Knowledge Access` enabled.
- Generated and reviewed files are stored in the same knowledge collection. `REVIEWER_AI_ASSISTANT_NAME` only affects the author name of DOCX comments.
- Users can review, access, download, and delete their generated or reviewed documents from their allowed knowledge collections. Deleting a document from a knowledge collection also removes it from the chats where it was generated.

<p align="center">
  <img src="../img/knowledge.png" alt="Knowledge Base Integration" />
</p>

### GenFiles Document Upload Settings

Behavior summary:

- If `ENABLE_CREATE_KNOWLEDGE=false`: GenFiles will **not** create or update knowledge collections. `KNOWLEDGE_COLLECTION_NAME` is ignored.
- If `ENABLE_CREATE_KNOWLEDGE=true`: GenFiles will create or update the knowledge collection named `KNOWLEDGE_COLLECTION_NAME` for the active user.

Collection naming:
- Generated files use `KNOWLEDGE_COLLECTION_NAME`.
- Reviewed DOCX files use the same `KNOWLEDGE_COLLECTION_NAME` collection.

## OpenAPI Tool Configuration in Open WebUI

**Requires Open WebUI >= 0.9.0.**

In Open WebUI, go to **Admin Panel > Settings > External Tools** and register a new tool with type `OpenApi`:

> URL: `http://host.docker.internal:8016`

<p align="center">
  <img src="../img/mcpconection.png" alt="Tool Configuration" />
</p>

> Once Tools are enabled for your model, Open WebUI gives you two ways to let your LLM call them: `Default Mode (Prompt-based)` or `Native Mode (Built-in function calling)`. See [OWUI Tools docs](https://docs.openwebui.com/features/extensibility/plugin/tools/) for details.

The recommended way is **`Native Mode (Built-in function calling)`**, as it provides better integration with the LLM's capabilities.

## Document Generation Setup

### System Prompt for your AI Assistant

For optimal results, create a custom agent in Open WebUI:

1. Create a new agent called **AI Assistant**
2. Use the system prompt from `example/systemprompt.md`
3. Set temperature to `0.5` for balanced creativity and accuracy
4. Enable Tools for the agent and select the GenFiles OpenAPI server, choosing `Native Mode (Built-in function calling)` for better integration.

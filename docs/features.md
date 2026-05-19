## Table of Contents

- [Features](#features)
- [Status / Compatibility](#status--compatibility)

## Features
- **File Generation**: Creates files in multiple formats (PowerPoint, Excel, Word, Markdown, PDF) from user requests.
- **OpenAPI Server**: Exposes tools via a standard HTTP OpenAPI interface for seamless integration with Open WebUI >= 0.9.0.
- **Python Templates**: Uses customizable Python templates to generate files with specific structures.
- **YAML-Based Structured Generation**: `ENABLE_STRUCTURED_YAML_MODE=true` activates structured YAML document builders for Word and PowerPoint, producing richer and more consistent output.
- **OWUI Integration**: Automatically uploads generated files to Open WebUI's file API (`/api/v1/files/`) and uses the knowledge APIs (`/api/v1/knowledge/search`, `/api/v1/knowledge/create`, `/api/v1/knowledge/{id}/file/add`) when knowledge persistence is enabled.
- **Document Review**: Analyzes existing Word documents and adds structured comments for corrections, grammar suggestions, or idea enhancements.
- **Image Embedding**: Supports embedding images from chat uploads directly into generated Word documents.
- **Knowledge Base Integration**: Generated and reviewed documents can be stored in Open WebUI knowledge collections for later access, download, deletion, and reuse from other chats.
- **Multi-User Support**: Each request is authenticated with the active user's bearer token, forwarded by Open WebUI, so documents are generated and uploaded on behalf of the correct user.

## Status / Compatibility

This release is **v0.4.0-alpha.5** and requires **Open WebUI >= 0.9.0**: [Open WebUI GitHub Repository](https://github.com/open-webui/open-webui)

The `ENABLE_CREATE_KNOWLEDGE` variable controls whether generated or reviewed files are automatically added to the user's knowledge collection. The base collection name is set with `KNOWLEDGE_COLLECTION_NAME`.

`ENABLE_STRUCTURED_YAML_MODE` enables the YAML-based structured builder for Word and PowerPoint generation.
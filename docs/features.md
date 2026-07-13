## Table of Contents

- [Features](#features)
- [Status / Compatibility](#status--compatibility)

## Features
- **File Generation**: Creates files in multiple formats (PowerPoint, Excel, Word, Markdown, PDF) from user requests.
- **OpenAPI Server**: Exposes tools via a standard HTTP OpenAPI interface for seamless integration with Open WebUI >= 0.9.0.
- **Python Templates**: Uses customizable Python templates to generate files with specific structures.
- **YAML-Based Structured Generation**: `ENABLE_STRUCTURED_YAML_MODE=true` activates structured YAML document builders for Word and PowerPoint, producing richer and more consistent output.
- **DOCX Style Presets**: The structured Word builder supports `style_doc: report` (one-column) and `style_doc: ieee` (two-column, indented) layouts.
- **Executive Charts for PowerPoint**: The structured PowerPoint builder supports chart intents such as `comparison`, `trend`, `distribution`, and `part_of_whole`, with chart types including `bar`, `line`, `area`, `pie`, `doughnut`, `combo`, and `waterfall`.
- **PowerPoint Themes & Visual Components**: Choose from multiple built-in themes, plus slide types like `stat_highlight` KPI cards, clean timelines, `content_latex` formulas, and image/text side layouts.
- **Inline Anthropic-Format Skill Instructions**: Each tool's description embeds the full template, YAML schema, or review workflow, so models receive complete authoring instructions directly without a separate skill-loading step.
- **OWUI Integration**: Automatically uploads generated files to Open WebUI's file API (`/api/v1/files/`) and uses the knowledge APIs (`/api/v1/knowledge/search`, `/api/v1/knowledge/create`, `/api/v1/knowledge/{id}/file/add`) when knowledge persistence is enabled.
- **Document Review**: Analyzes existing Word documents and adds structured comments for corrections, grammar suggestions, or idea enhancements.
- **Image Embedding**: Supports embedding images from chat uploads directly into generated Word documents.
- **Knowledge Base Integration**: Generated and reviewed documents can be stored in Open WebUI knowledge collections for later access, download, deletion, and reuse from other chats.
- **Multi-User Support**: Each request is authenticated with the active user's bearer token, forwarded by Open WebUI, so documents are generated and uploaded on behalf of the correct user.
- **Optimized Docker Build**: Dockerfile uses layer caching and an unprivileged user; Docker Compose supports `watch` sync and a healthcheck for faster local development.

## Status / Compatibility

This release is **v0.4.0-alpha.6** and requires **Open WebUI >= 0.9.0**: [Open WebUI GitHub Repository](https://github.com/open-webui/open-webui)

The `ENABLE_CREATE_KNOWLEDGE` variable controls whether generated or reviewed files are automatically added to the user's knowledge collection. The base collection name is set with `KNOWLEDGE_COLLECTION_NAME`.

`ENABLE_STRUCTURED_YAML_MODE` enables the YAML-based structured builder for Word and PowerPoint generation.
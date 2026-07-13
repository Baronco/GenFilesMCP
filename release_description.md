# v0.4.0-alpha.6 Documentation Sync & New Capabilities 🚀

This release synchronizes all user-facing documentation and version references with the `v0.4.0-alpha.6` image, and surfaces the capabilities that have landed since `v0.4.0-alpha.5`.

---

## Highlights & Objectives 📌

- **What changed**
  - **Project restructure**: The codebase was reorganized into high-cohesion modules (`api/`, `tools/pptx/`, `utils/builders/`, `utils/config/`, `utils/http/`, `utils/models/`) to improve maintainability.
  - **Executive charts for PowerPoint**: The YAML-based PPTX builder now supports a broad set of chart intents (`comparison`, `trend`, `distribution`, `part_of_whole`) and chart types including `bar`, `line`, `area`, `pie`, `doughnut`, `combo`, and `waterfall`.
  - **DOCX YAML styles**: The structured Word builder gained `style_doc: report | ieee`, making it easy to switch between a one-column report layout and a two-column IEEE-style paper layout.
  - **PPTX visual refresh**: New themes, cleaner timelines, `stat_highlight` KPI cards, improved `content_latex` slides, and better image/text side layouts.
  - **Skill-format instructions**: Tool instructions are now delivered inline as Anthropic-style skills, so models receive the full template/schema directly when inspecting each tool.
  - **Optimized Docker build**: The Dockerfile leverages layer caching and the compose file adds `watch` sync and a healthcheck for a faster local development loop.
- **Why**
  - Keep documentation accurate and consistent with the published Docker image.
  - Help users discover the new structured-generation capabilities without reading source code.
  - Reduce deployment friction with clearer installation and release notes.
- **Compatibility**
  - Requires **Open WebUI >= 0.9.0**.
  - Set `ENABLE_FORWARD_USER_INFO_HEADERS=True` in Open WebUI so GenFiles receives the active user's bearer token.

- **Pull the pre-built Docker image from GitHub Container Registry:**

```bash
docker pull ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.6
```

- **Run the container:**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.6
```

- **One-line command (copy/paste):**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT -e OWUI_URL="http://host.docker.internal:3000" -e PORT=YOUR_PORT -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" -e ENABLE_CREATE_KNOWLEDGE=false --name gen_files_mcp ghcr.io/baronco/genfiles-openapi:v0.4.0-alpha.6
```

---

# v0.3.0-alpha.6 Return to MCP Server, Reviewer Name Variable & DOCX Tool Improvements 🚀

This release returns GenFiles to native MCP Server mode (`streamable-http`) and keeps the same session-based authentication flow. The DOCX generation path is refined so models focus on planning document elements and content (instead of generating full Python code).

---

## Highlights & Objectives 📌

- **What changed**
  - **Back to MCP Server:** This alpha returns from OpenAPI Tool Server mode to MCP Server mode for Open Web UI native tool calling.
  - **New environment variable:** Added `REVIEWER_AI_ASSISTANT_NAME` to control the assistant name used in DOCX review comments.
  - **DOCX generation compatibility improvements:** Updated Word generation inputs and handling to improve cross-model compatibility and reduce failure caused by code-heavy outputs.
  - **Same behavior for other tools:** PowerPoint, Excel, Markdown generation and DOCX review remain functionally aligned with previous behavior (they still execute generated code); the reduced code-heavy approach applies specifically to DOCX generation.
- **Why**
  - Improve model compatibility by reducing dependency on fully generated code.
  - Let AI assistants focus on defining logical document elements and their content.
  - Keep existing non-DOCX tools stable while improving document authoring reliability.
- **Model evaluation summary (Example 1: Generating a DOCX file)**
  - A benchmark was conducted to evaluate whether multiple models can generate a DOCX document with a paper-like double-column format about the gradient descent concept, including images, equations, tables, and other structured elements.
  - The objective of this benchmark was to validate tool use, structural quality, and first-pass execution when models define document elements/content instead of generating 100% of the Python code.
  - Full model-by-model results are available in: [Benchmark Results](https://github.com/Baronco/GenFilesMCP/tree/dev?tab=readme-ov-file#example-1-generating-a-docx-file)
- **Roadmap direction**
  - Continue reducing code-generation burden for AI models.
  - Expand workflows where assistants only plan document structure, logical elements, and content definitions.

- **Pull the pre-built Docker image from GitHub Container Registry:**

```bash
docker pull ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.6
```

- **Run the container:**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.6
```

- **One-line command (copy/paste):**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT -e OWUI_URL="http://host.docker.internal:3000" -e PORT=YOUR_PORT -e REVIEWER_AI_ASSISTANT_NAME="GenFilesMCP" -e ENABLE_CREATE_KNOWLEDGE=false --name gen_files_mcp ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.6
```

---

# v0.3.0-alpha.4 Schema Simplification for improve compatibility  with Claude, GPT, Gemini and Grok Models 🚀

The MCP Server now is a OpenAPI Tool Server that generates Word documents using a simplified schema with flattened content models. This change enhances compatibility with various AI models by reducing nested structures and using plain dictionaries for document elements.

📌 **In OWUI you have to use this alpha as OpenApi Tool Server, not as MCP Server.** Authentication by user session remains the same.

📌 The generation of powerpoint, excel and markdown files and docx review functionality remain unchanged.

- **Pull the pre-built Docker image from GitHub Container Registry:**

```bash
docker pull ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.4
```

- **Run the container:**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.4
```

---

# v0.3.0-alpha.3 Structured Document Generation & Equation Support 🚀

Replaced dynamic code execution in Word document generation with a secure, structured dictionary-based approach using Pydantic validation. Added math2docx for accurate equation rendering, enhancing safety and accessibility for various AI models.

---

## Highlights & Objectives 📌

- **What changed**
  - **Structured Generation:** Radical shift from executing AI-generated Python scripts to using validated Pydantic models for document schemas. The new `generate_word` tool accepts a structured dictionary with metadata, a section containing optional paragraph, list, table, image, and equation, eliminating code execution risks.
  - **Equation Support:** Integrated `math2docx` package to enable proper LaTeX equation rendering in Word documents, ensuring mathematical notation is preserved accurately, [github link](https://github.com/keh9mark/math2docx).
  - **Security & Simplicity:** Removed `python exec` calls, focusing on content and styling rather than dynamic scripting. This reduces errors and allows models with varying programming capabilities to generate documents reliably.
- **Why**
  - Enhance security by avoiding execution of AI-generated code, preventing potential vulnerabilities.
  - Simplify document creation by letting AI focus on structured content, improving consistency and reducing back-and-forth clarifications.
  - Enable broader model compatibility, as generation no longer relies heavily on coding skills, making the system more accessible and robust.
- **Compatibility**
  - Requires **Open Web UI v0.6.42+** (due to knowledge API changes).
  - For OWUI < v0.6.42 use GenFilesMCP **<= 0.2.2**.
  - **MCPO:** alpha is currently **not compatible** with MCPO; compatibility depends on PR https://github.com/open-webui/mcpo/pull/273 (adds per-session bearer token header support). Goal: full MCPO compatibility once that PR is merged.

- **Pull the pre-built Docker image from GitHub Container Registry:**

```bash
docker pull ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.3
```

- **Run the container:**

```bash
docker run -d --restart unless-stopped -p YOUR_PORT:YOUR_PORT \
  -e OWUI_URL="http://host.docker.internal:3000" \
  -e PORT=YOUR_PORT \
  -e ENABLE_CREATE_KNOWLEDGE=false \
  --name gen_files_mcp \
  ghcr.io/baronco/genfilesmcp:v0.3.0-alpha.3
```

---

# v0.3.0-alpha.2 Image Embedding in DOCX & Enhanced Agent Behavior 🚀

Added support for embedding images directly into generated Word documents from chat uploads. Updated system prompt for more autonomous document generation and improved `chat_context` tool to retrieve image metadata.

---

## Highlights & Objectives 📌

- **What changed**
  - **Image Embedding:** New capability to include images uploaded to the chat in generated DOCX files. Images are embedded seamlessly, preserving order and context.
  - **System Prompt Update:** Enhanced FileGenAgent prompt to reduce clarification requests, allowing the model to make assumptions and proceed autonomously for better user experience.
  - **chat_context Tool:** Now retrieves image IDs and metadata from chat messages, enabling access to uploaded images for document generation.
- **Why**
  - Enable richer, visual content in documents without external dependencies.
  - Improve efficiency by minimizing back-and-forth interactions, letting the AI infer and generate based on context.
  - Streamline image handling for more dynamic and context-aware file creation.
- **Compatibility**
  - Requires **Open Web UI v0.6.42+** (due to knowledge API changes).
  - For OWUI < v0.6.42 use GenFilesMCP **<= 0.2.2**.
  - **MCPO:** alpha is currently **not compatible** with MCPO; compatibility depends on PR https://github.com/open-webui/mcpo/pull/273 (adds per-session bearer token header support). Goal: full MCPO compatibility once that PR is merged.

  ---

  # v0.3.0-alpha.1 Knowledge API update & alpha release 💡

Updated knowledge integration to use the paginated `/api/v1/knowledge/search` endpoint (requires Open Web UI v0.6.42+). Note: this alpha is not compatible with MCPO yet compatibility depends on https://github.com/open-webui/mcpo/pull/273.

---

## Highlights & Objectives 📌

- **What changed**
  - Switched to paginated knowledge search: `/api/v1/knowledge/search` (supports `query` + pages).
  - Added support for searching by collection name (`knowledge_name`) before creating collections.
  - Robust pagination handling (fetches pages until complete) and response normalization.
- **Why**
  - Align with Open Web UI API changes in v0.6.42 and avoid breaking knowledge operations.
- **Compatibility**
  - Requires **Open Web UI v0.6.42+**.
  - For OWUI < v0.6.42 use GenFilesMCP **<= 0.2.2**.
  - **MCPO:** alpha is currently **not compatible** with MCPO; compatibility depends on PR https://github.com/open-webui/mcpo/pull/273 (adds per-session bearer token header support). Goal: full MCPO compatibility once that PR is merged.

---

# Release Notes for v0.2.2 💡

## What's Changed

This release focuses on fixing file upload errors to knowledge collections, improving documentation, and enhancing overall robustness for deployments using `ENABLE_CREATE_KNOWLEDGE=true`.

### Bug Fixes
- **Fixed file upload errors to knowledge collections**: Resolved issues when uploading files to Open Web UI knowledge collections by changing API parameters from boolean to string values (`"true"` and `"false"`). This fix is derived from [Open Web UI Discussion #15192](https://github.com/open-webui/open-webui/discussions/15192), ensuring compatibility with RAG workflows while allowing knowledge collection creation. 🙇‍♂️

### Documentation and Deployment Improvements
- **Expanded README.md**: Added comprehensive setup instructions, troubleshooting notes for Open Web UI v0.6.40 (including workaround for "Function Name Filter List" field), new Docker Compose deployment option, and additional usage examples for Excel and PowerPoint generation. Updated version references to v0.2.2. 
- **Added docker-compose.yml**: Included a new Docker Compose file for easier local builds and deployments with environment variable configuration @gdshadow01  👍
- **Added License section**: Included MIT License reference in README.md

### Knowledge Collection Integration
- **Enhanced knowledge utilities**: Refactored knowledge.py to use a nested dictionary structure for better tracking of user knowledge collections, improving robustness and extensibility. 

### Agent Prompt and Usage Guidance
- **Rewrote system prompt**: Completely revised systemprompt.md with clearer operational rules, output requirements, and file handling standards. Emphasized professional output, strict format adherence, and added constraints to prevent overpromising capabilities. 🤖

### Project Metadata and Minor Fixes
- **Updated pyproject.toml**: Bumped version to v0.2.2 and ensured project name consistency. 
- **Fixed typos in server.py**: Corrected "Recieved" to "Received" in log messages across multiple endpoints. 

### New Contributors
- @gdshadow01  made their first contribution in this release! 🎉 ありがとうございます！🙇‍♂️

>**Note**: If you encounter any issues with `ENABLE_CREATE_KNOWLEDGE=true`, set it to `false` temporarily; file generation and review capabilities remain unaffected. Please report issues for further review.

GenFiles is an OpenAPI server that enables AI assistants to generate PowerPoint, Excel, Word, Markdown, and PDF files based on user instructions. It can also review existing Word documents by analyzing their structure and adding inline comments.

## Available tools

### File generation
- `generate_powerpoint` — generate a PowerPoint presentation using a Python script
- `generate_powerpoint_structured_yaml` — generate a PowerPoint presentation from a structured YAML definition
- `generate_excel` — generate an Excel workbook using a Python script
- `generate_markdown` — generate a Markdown document using a Python script
- `generate_word` — generate a Word document using a Python script
- `generate_word_structured_yaml` — generate a Word document from a structured YAML definition
- `generate_pdf` — generate a PDF document using a Python script

### Word document review
- `list_docx_elements` — inspect the structure of an existing Word document (index, style, and text of each element)
- `review_docx` — add targeted inline comments to specific elements of a Word document

### Chat file utilities
- `fetch_uploaded_chat_file_ids` — retrieve the IDs of all files and images uploaded in the current chat session

## Important workflow rules

> **Before generating any PowerPoint or Word document that may include images, always call `fetch_uploaded_chat_file_ids` first** to check whether the user has uploaded images in the conversation. Use the returned file IDs as `image_id` references in the YAML or script. Skip this step only when the user explicitly confirms there are no images to include.

> **LaTeX equations must only go inside math-specific elements** (`content_latex` slides in PowerPoint, `equation` elements in Word). Placing LaTeX syntax in regular text fields renders as raw broken characters on the final document.

> **LaTeX expressions must use only plain ASCII LaTeX commands. Never substitute Unicode characters for LaTeX commands inside math.** For example, write `\hat{y}` not `ŷ`, write `\bar{x}` not `x̄`, write `\beta` not `β`. Unicode math symbols embedded in LaTeX strings break the YAML parser before the document is even built.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.
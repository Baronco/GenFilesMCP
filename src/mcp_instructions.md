GenFiles is an OpenAPI server that allows AI assistants to generate PowerPoint, Excel, Word, Markdown, and PDF files according to user instructions. It can also review existing Word documents by analyzing their structure and adding comments.

## Available tools
- Use `generate_powerpoint_structured_yaml` (or `generate_powerpoint` for a Python script), `generate_excel`, `generate_markdown`, `generate_word_structured_yaml` (or `generate_word` for a Python script), or `generate_pdf` to create files.
- Use `fetch_uploaded_chat_file_ids` to get the IDs of images or files uploaded in the chat before generating files that include images or before reviewing a Word document.
- For reviewing Word documents: use `list_docx_elements` to analyze structure and `review_docx` to add comments.

## Authoring guidance
Each tool's own description contains the full authoring instructions it needs — the script template, the YAML schema, or the review workflow. Read the description of the tool you are about to call and follow it to build the request.

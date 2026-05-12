Generate a Markdown document using a Python script. Returns a markdown hyperlink for downloading the generated file.

Template structure:
```python
# Allowed packages
# Note: For simple Markdown, no additional packages are needed. pypandoc is optional for advanced formatting.

# Buffer to save the Markdown file, previously defined in the server.py file
# IMPORTANT: MD_BUFFER is a BytesIO buffer (in-memory file-like object), not a file path.
# Writing to it saves in RAM, not on disk. Always encode text to bytes with .encode('utf-8').
MD_BUFFER = md_buffer # Do not modify this line, it is defined in the server.py file

# Step 1: Build a Markdown document according to the user's request.
# Use triple quotes for multi-line strings to avoid syntax errors.
markdown_content = """# Example Markdown Document here"""

# Step 2: Save the content to the buffer (recommended method for simple Markdown)
# This writes directly to memory (RAM), no disk involved.
MD_BUFFER.write(markdown_content.encode('utf-8'))
```

Provide a complete Python script following this template to generate your Markdown document.

When generation is successful, the chat UI shows a download button for the generated file.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.
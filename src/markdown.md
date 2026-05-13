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
# Use a plain string literal and escape newlines with \n if needed.
markdown_content = "# Example Markdown Document here"

# Step 2: Save the content to the buffer (recommended method for simple Markdown)
# This writes directly to memory (RAM), no disk involved.
MD_BUFFER.write(markdown_content.encode('utf-8'))
```

Provide a complete Python script following this template to generate your Markdown document.

> **Reminder:** keep the buffer assignment line `MD_BUFFER = md_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.
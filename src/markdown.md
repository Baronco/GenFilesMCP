Generate a Markdown (.md) file with a Python script. On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_markdown` (`python_script`, `file_name`). Plain text only — cannot embed binary images.

## Example
```python
MD_BUFFER = md_buffer                # keep this line exactly

content = "# Title\n\nBody text with **bold** and a list:\n\n- item 1\n- item 2\n"
MD_BUFFER.write(content.encode("utf-8"))   # write bytes
```

## Rules
- Keep `MD_BUFFER = md_buffer` exactly.
- Write bytes: `.encode("utf-8")`.
- Plain text only; no binary images.

Generate a Markdown (.md) file with a Python script. {{SUCCESS_DELIVERY_RULE}}

CANNOT embed charts or images. Call `generate_markdown` (`python_script`, `file_name`).

## Example
```python
MD_BUFFER = md_buffer                # keep this line exactly
content = "# Title\n\nBody text with **bold** and a list:\n\n- item 1\n- item 2\n"
MD_BUFFER.write(content.encode("utf-8"))
```

## Rules
- Keep `MD_BUFFER = md_buffer` exactly.
- Write bytes: `.encode("utf-8")`.

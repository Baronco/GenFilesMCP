---
name: word-generation
description: Generate or review a Word (.docx) document — Python-script generation, structured YAML generation, or reviewing an existing document with comments.
---

# Word (.docx) — generation & review

Use this skill whenever the user wants a Word document **created** or an existing one **reviewed**. Pick a mode below.

**Before generating or reviewing**, call `fetch_uploaded_chat_file_ids` to get the IDs of files/images uploaded in the chat: image IDs feed generation (`images_list`); the uploaded `.docx` file ID feeds review.

**Which tool to call**
- Python generation → `generate_word` (`python_script`, `file_name`, `images_list`).
- YAML generation → `generate_word_structured_yaml` (`document_yaml`, `file_name`).
- Review → `list_docx_elements`, then `review_docx`.

---

## Mode 1 — Python-script generation

Generate a Word document using a Python script. Returns a markdown hyperlink for downloading the generated file.

Template structure:
```python
# Allowed packages
import numpy as np
from docx import Document
from io import BytesIO
from docx.shared import Inches

# Import here other docx packages you need, but do not import other packages that are not allowed.

# Buffer to save the docx file, previously defined in the server.py file
DOCX_BUFFER = docx_buffer # Do not modify this line, it is defined in the server.py file

# Width in inches for the image to be added
width = 2  # Example width, modify as needed

# If images are needed, they would be preloaded by the server and passed here.
LIST_OF_BYTES_IO_IMAGES = images #  # Do not modify this line if images are needed, it is defined in the server.py file 


# Initialize a new Document instance
doc = Document()

# Example title
doc.add_heading("Example of report", level=1)

# Ensure the pointer is at the start
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
# Example of adding the first image from the list to the document
doc.add_picture(
    LIST_OF_BYTES_IO_IMAGES[0],  
    width=Inches(width)
)

# Generate here the necessary transformations for generating the word document to the user's request. 

# Save the presentation
doc.save(DOCX_BUFFER) # Do not modify this line, it is defined in the server.py file
```

Provide a complete Python script following this template to generate your Word document.

> **Reminder:** keep the buffer assignment line `DOCX_BUFFER = docx_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.

### Optional — generate or edit images with seaborn / pillow

`scipy`, `seaborn`, `matplotlib`, and `pillow` are also available. You can render a chart or edit an image **in memory** and append it to `LIST_OF_BYTES_IO_IMAGES` (the same list that holds uploaded images), then place it with `doc.add_picture(...)`:

```python
import io, matplotlib
matplotlib.use("Agg")              # headless backend
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(6, 4))
sns.barplot(x=["A", "B", "C"], y=[3, 7, 5], ax=ax)
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150, bbox_inches="tight"); plt.close(fig); buf.seek(0)
LIST_OF_BYTES_IO_IMAGES.append(buf)            # add the generated image to the list
LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
doc.add_picture(LIST_OF_BYTES_IO_IMAGES[-1], width=Inches(5))
```

To edit an uploaded image instead: open `LIST_OF_BYTES_IO_IMAGES[i]` with `PIL.Image`, edit, save to a new `BytesIO`, `seek(0)`, `append`, then `add_picture`. Always `seek(0)` right before adding (it consumes the stream).

---

## Mode 2 — YAML structured generation

Use this tool to createa a Word document from a structured YAML definition.

## YAML structure

Use a raw YAML body with the following top-level keys:

- `cover`: Document cover metadata.
- `columns_body`: Optional number of columns in the body content (`1` or `2`).
- `body`: Ordered YAML list of document elements.

Each element must include a `type` field. Supported element types:
- `header`
- `paragraph`
- `list`
- `table`
- `image`
- `equation`
- `page_break`

## Field details:

- `cover`: Required object with `title`, `subtitle`, `description`, `author`, `month`, `year`, `page_break`.
- `columns_body`: Integer value defining layout columns. If omitted, defaults to `1`.
- `body`: List of ordered elements.

## Element details:

- `header`
  - `text`: Heading text.
  - `level`: Heading level between `1` and `6`.

- `paragraph`
  - `text`: Paragraph content. Supports inline Markdown emphasis with `**bold**` and `*italic*`.

- `list`
  - `style`: `bullet` or `numbered`.
  - `items`: A YAML list of strings.

- `table`
  - `headers`: List of column header strings.
  - `rows`: List of rows, each row is a list of strings.
  - `caption`: Optional table caption.

- `image`
  - `id`: Exact uploaded image file ID.
  - `caption`: Optional caption for the image.

- `equation`
  - `latex`: LaTeX expression (e.g., "E = mc^{2}")
  - `caption`: Optional caption.
  - **Always use pure ASCII LaTeX commands inside `latex` — never substitute Unicode characters for LaTeX symbols.** Write `\hat{y}` not `ŷ`, `\bar{x}` not `x̄`, `\beta` not `β`. Unicode math characters embedded in LaTeX strings corrupt the YAML before the document is built.

- `page_break`
  - No additional fields required.

## Important notes:

- Always use `yaml.safe_load` in the backend parser.
- Do not mix JSON-style objects in the YAML body; use valid YAML syntax.
- Keep image IDs exact and unchanged.
- Use `page_break: true` in the `cover` section to start body content on a new page.

> When generation is successful, the chat UI shows a download button for the generated file. Do not output or mention download links in the assistant response.

---

## Mode 3 — Review an existing document

Review adds targeted comments to an existing `.docx` (spelling, grammar, style, clarity). Two steps, after getting the document's file ID.

**Step 0 — get the file ID:** call `fetch_uploaded_chat_file_ids` to obtain the uploaded `.docx` `file_id` and its original name.

**Step 1 — inspect the structure (`list_docx_elements`):** call with `file_id` and `file_name`. It returns each element's **index**, style, and text. Use the indexes to decide which elements to comment on.

**Step 2 — add comments (`review_docx`):** call with `file_id`, `file_name`, and `review_comments` = a list of `{'index': <int>, 'comment': <str>}` objects, where `index` is an element index from step 1. Example:

```json
[{"index": 0, "comment": "Fix typo: 'teh' -> 'the'"},
 {"index": 5, "comment": "This sentence is unclear; consider splitting it."}]
```

Only comment where it genuinely improves the document; keep each comment specific and actionable.

Generate a Word (.docx) with a Python script (`python-docx`). On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_word` (`python_script`, `file_name`, `images_list`). For uploaded images, call `fetch_uploaded_chat_file_ids` first; the server preloads them into `LIST_OF_BYTES_IO_IMAGES`.

## Example
```python
from docx import Document
from docx.shared import Inches

DOCX_BUFFER = docx_buffer           # keep this line exactly
LIST_OF_BYTES_IO_IMAGES = images    # keep this line exactly (preloaded images)

doc = Document()
doc.add_heading("Report", level=1)
# Build the document per the user's request.
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
doc.add_picture(LIST_OF_BYTES_IO_IMAGES[0], width=Inches(4))
doc.save(DOCX_BUFFER)               # keep this line exactly
```

## Rules
- Keep `DOCX_BUFFER = docx_buffer` and `doc.save(DOCX_BUFFER)` exactly; renaming breaks the script.
- `seek(0)` an image buffer right before `add_picture`.
- To add a generated chart: render with matplotlib/seaborn to a `BytesIO`, `seek(0)`, append to `LIST_OF_BYTES_IO_IMAGES`, then `add_picture`. Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

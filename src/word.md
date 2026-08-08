Generate a Word (.docx) with a Python script (`python-docx`). {{SUCCESS_DELIVERY_RULE}}

Call `generate_word` (`python_script`, `file_name`, `images_list`). Uploaded images: call `fetch_uploaded_chat_file_ids` first; server preloads into `LIST_OF_BYTES_IO_IMAGES`.

## Example
```python
from docx import Document
from docx.shared import Inches

DOCX_BUFFER = docx_buffer           # keep this line exactly
LIST_OF_BYTES_IO_IMAGES = images    # keep this line exactly (preloaded images)

doc = Document()
doc.add_heading("Report", level=1)
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
doc.add_picture(LIST_OF_BYTES_IO_IMAGES[0], width=Inches(4))
doc.save(DOCX_BUFFER)               # keep this line exactly

# Chart via seaborn/matplotlib
import io, seaborn as sns
fig = sns.barplot(x=["A", "B", "C"], y=[10, 20, 15])
buf = io.BytesIO(); fig.figure.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
LIST_OF_BYTES_IO_IMAGES.append(buf)
LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
doc.add_picture(LIST_OF_BYTES_IO_IMAGES[-1], width=Inches(4))
```

## Rules
- Keep `DOCX_BUFFER = docx_buffer` and `doc.save(DOCX_BUFFER)` exactly; `seek(0)` before each `add_picture`.
- Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

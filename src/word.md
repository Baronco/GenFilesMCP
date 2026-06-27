Generate a Word (.docx) document using a **Python script** (`python-docx`). Returns a markdown hyperlink for downloading the generated file.

Before generating a document that embeds uploaded images, call `fetch_uploaded_chat_file_ids` to get their IDs; the server preloads those images into `LIST_OF_BYTES_IO_IMAGES`.

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

# Save the document
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

Generate a PowerPoint (.pptx) presentation using a **Python script** (`python-pptx`). Returns a markdown hyperlink for downloading the generated file.

Before generating a deck that embeds uploaded images, call `fetch_uploaded_chat_file_ids` to get their IDs; the server preloads those images into `LIST_OF_BYTES_IO_IMAGES`.

Template structure:
```python
# Allowed packages
import numpy as np
from pptx import Presentation
from pptx.util import Inches, Pt

# Import here other pptx packages you need, but do not import other packages that are not allowed.

# Buffer to save the PowerPoint file, previously defined in the server.py file
PPTX_BUFFER = pptx_buffer # Do not modify this line, it is defined in the server.py file

# Width in inches for the image to be added
width = 2  # Example width, modify as needed

# If images are needed, they would be preloaded by the server and passed here.
LIST_OF_BYTES_IO_IMAGES = images #  # Do not modify this line if images are needed, it is defined in the server.py file

# Initialize a new Presentation instance
prs = Presentation()

# slides ratio has to be 16:9 not 4:3
prs.slide_width = Inches(13.333333)
prs.slide_height = Inches(7.5)

# Generate here the necessary transformations for generating the PowerPoint presentation according to the user's request. Use titles, subtitles, diagrams, tables, colors, clear fonts, and other elements to make the presentation visually appealing and easy to understand.

# Ensure the pointer is at the start
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
# Example of adding the first image from the list to the presentation, modify the left and top parameters as needed to position the image correctly on the slide
prs.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[0], left=Inches(5.2), top=Inches(1.2), width=Inches(width))

# Save the presentation
prs.save(PPTX_BUFFER) # Do not modify this line, it is defined in the server.py file
```

Provide a complete Python script following this template to generate your PowerPoint presentation.

> **Reminder:** keep the buffer assignment line `PPTX_BUFFER = pptx_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.

### Optional — generate or edit images with seaborn / pillow

`scipy`, `seaborn`, `matplotlib`, and `pillow` are also available. You can render a chart or edit an image **in memory** and append it to `LIST_OF_BYTES_IO_IMAGES` (the same list that holds uploaded images), then place it with `prs.shapes.add_picture(...)`:

```python
import io, matplotlib
matplotlib.use("Agg")              # headless backend
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.lineplot(x=[1, 2, 3, 4], y=[10, 14, 9, 18], marker="o", ax=ax)
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150, bbox_inches="tight"); plt.close(fig); buf.seek(0)
LIST_OF_BYTES_IO_IMAGES.append(buf)            # add the generated image to the list
LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[-1], left=Inches(2), top=Inches(1.5), width=Inches(9))
```

To edit an uploaded image instead: open `LIST_OF_BYTES_IO_IMAGES[i]` with `PIL.Image`, edit, save to a new `BytesIO`, `seek(0)`, `append`, then `add_picture`. Always `seek(0)` right before adding (it consumes the stream).

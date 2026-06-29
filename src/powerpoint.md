Generate a PowerPoint (.pptx) with a Python script (`python-pptx`). On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_powerpoint` (`python_script`, `file_name`, `images_list`). For uploaded images, call `fetch_uploaded_chat_file_ids` first; the server preloads them into `LIST_OF_BYTES_IO_IMAGES`.

## Example
```python
from pptx import Presentation
from pptx.util import Inches

PPTX_BUFFER = pptx_buffer           # keep this line exactly
LIST_OF_BYTES_IO_IMAGES = images    # keep this line exactly (preloaded images)

prs = Presentation()
prs.slide_width = Inches(13.333)    # 16:9
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
# Build slides per the user's request.
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
slide.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[0], Inches(2), Inches(1.5), width=Inches(9))
prs.save(PPTX_BUFFER)               # keep this line exactly
```

## Rules
- Keep `PPTX_BUFFER = pptx_buffer` and `prs.save(PPTX_BUFFER)` exactly.
- Use 16:9 (`13.333 x 7.5` inches).
- `seek(0)` an image buffer right before `add_picture`.
- To add a generated chart: render with matplotlib/seaborn to a `BytesIO`, `seek(0)`, append to `LIST_OF_BYTES_IO_IMAGES`, then `add_picture`. Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

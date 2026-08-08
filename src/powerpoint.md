Generate a PowerPoint (.pptx) with a Python script (`python-pptx`). {{SUCCESS_DELIVERY_RULE}}

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
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
slide.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[0], Inches(2), Inches(1.5), width=Inches(9))
prs.save(PPTX_BUFFER)               # keep this line exactly

# Chart via seaborn/matplotlib
import io, seaborn as sns
fig = sns.barplot(x=["A", "B", "C"], y=[10, 20, 15])
buf = io.BytesIO(); fig.figure.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
LIST_OF_BYTES_IO_IMAGES.append(buf)
LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
slide.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[-1], Inches(2), Inches(1.5), width=Inches(9))
```

## Rules
- Keep `PPTX_BUFFER = pptx_buffer` and `prs.save(PPTX_BUFFER)` exactly.
- Use 16:9 (`13.333 x 7.5` inches).
- `seek(0)` an image buffer right before `add_picture`.
- Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

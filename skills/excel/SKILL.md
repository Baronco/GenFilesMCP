---
name: excel-generation
description: Generate an Excel (.xlsx) workbook from a Python script using openpyxl — tables, formatting, formulas, and charts.
---

# Excel (.xlsx) generation

Generate an `.xlsx` workbook with a Python script. Call `generate_excel` (`python_script`, `file_name`). Excel does not take a preloaded image list; call `fetch_uploaded_chat_file_ids` only if the request references files already uploaded in the chat.

Generate an Excel workbook using a Python script. Returns a markdown hyperlink for downloading the generated file.

Template structure:
```python
# Allowed packages
import numpy as np
from openpyxl import Workbook

# Import here other xlsx packages you need, but do not import other packages that are not allowed.

# Buffer to save excel file, previously defined in the server.py file
XLSX_BUFFER = xlsx_buffer # Do not modify this line, it is defined in the server.py file

# Initialize a new Workbook instance
wb = Workbook()

# Apply the required data transformations to build the Excel workbook based on the user's request.
# Create the necessary worksheets, populate tables, add charts, and format cells for clarity and visual appeal.

# Save the Excel workbook
wb.save(XLSX_BUFFER) # Do not modify this line, it is defined in the server.py file
```

Provide a complete Python script following this template to generate your Excel workbook.

> **Important:** Keep the buffer assignment line `XLSX_BUFFER = xlsx_buffer` exactly as shown. If you omit or rename it, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.

### Optional — embed a chart image with seaborn / pillow

`scipy`, `seaborn`, `matplotlib`, and `pillow` are also available. Excel has **no preloaded image list** (unlike Word/PowerPoint/PDF). Prefer native `openpyxl.chart` objects (they stay editable in Excel); if you want a seaborn-styled figure, render it in memory and embed it via `openpyxl.drawing.image.Image`:

```python
import io, matplotlib
matplotlib.use("Agg")              # headless backend
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl.drawing.image import Image as XLImage

ws = wb.active
fig, ax = plt.subplots(figsize=(6, 4))
sns.barplot(x=["A", "B", "C"], y=[3, 7, 5], ax=ax)
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150, bbox_inches="tight"); plt.close(fig); buf.seek(0)
ws.add_image(XLImage(buf), "E2")
```

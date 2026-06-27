Generate an Excel (.xlsx) with a Python script (`openpyxl`). On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_excel` (`python_script`, `file_name`). Excel has NO preloaded image list.

## Example
```python
from openpyxl import Workbook

XLSX_BUFFER = xlsx_buffer            # keep this line exactly

wb = Workbook()
ws = wb.active
# Build sheets, tables, formulas, and charts per the user's request.
wb.save(XLSX_BUFFER)                 # keep this line exactly
```

## Rules
- Keep `XLSX_BUFFER = xlsx_buffer` and `wb.save(XLSX_BUFFER)` exactly.
- Prefer native `openpyxl.chart` objects (they stay editable in Excel).
- To embed a seaborn figure: render to a `BytesIO`, `seek(0)`, add via `openpyxl.drawing.image.Image`. Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

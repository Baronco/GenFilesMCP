Generate an Excel (.xlsx) with a Python script (`openpyxl`). {{SUCCESS_DELIVERY_RULE}}

Call `generate_excel` (`python_script`, `file_name`). No preloaded image list.

## Example
```python
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

XLSX_BUFFER = xlsx_buffer            # keep this line exactly

wb = Workbook()
ws = wb.active
# Populate cells, then build chart.
chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_row=5)
chart.add_data(data, titles_from_data=True)
ws.add_chart(chart, "A1")
wb.save(XLSX_BUFFER)                 # keep this line exactly
```

## Rules
- Keep `XLSX_BUFFER = xlsx_buffer` and `wb.save(XLSX_BUFFER)` exactly.
- Use native `openpyxl.chart` objects — they stay editable in Excel.
- Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

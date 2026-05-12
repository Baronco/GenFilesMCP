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

When generation is successful, the chat UI shows a download button for the generated file.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.
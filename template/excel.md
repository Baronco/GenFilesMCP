# Allowed packages
import numpy as np
from openpyxl import Workbook

# Import here other xlsx packages you need, but do not import other packages that are not allowed.

# Path to save excel file, previously defined in the server.py file
XLSX_PATH = xlsx_path # Don not modify this line, it is defined in the server.py file

def excel():
    # Initialize a new Workbook instance
    wb = Workbook()

    # Apply the required data transformations to build the Excel workbook based on the user's request.
    # Create the necessary worksheets, populate tables, add charts, and format cells for clarity and visual appeal.

    # Save the Excel workbook
    wb.save(XLSX_PATH) # Don not modify this line, it is defined in the server.py file

    # Check if the file was created successfully
    if not os.path.exists(XLSX_PATH):
        raise ValueError(f"Failed to create the excel file.")
    else:
        return f"Excel file created successfully!"


# Invoke the function to generate the Excel file
excel()
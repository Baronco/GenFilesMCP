Generate a Word document using a Python script. Returns a markdown hyperlink for downloading the generated file.

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

# Save the presentation
doc.save(DOCX_BUFFER) # Do not modify this line, it is defined in the server.py file
```

Provide a complete Python script following this template to generate your Word document.

> **Reminder:** keep the buffer assignment line `DOCX_BUFFER = docx_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.
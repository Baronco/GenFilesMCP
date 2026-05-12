Generate a PowerPoint presentation using a Python script. Returns a markdown hyperlink for downloading the generated file.

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

When generation is successful, the chat UI shows a download button for the generated file.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.
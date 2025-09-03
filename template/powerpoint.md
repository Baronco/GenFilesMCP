def power_point():

    # Allowed packages
    import numpy as np
    from pptx import Presentation

    # Import here other pptx packages you need, but do not import other packages that are not allowed.

    # Path to save the PowerPoint file, previously defined in the server.py file
    PPTX_PATH = pptx_path # Don not modify this line, it is defined in the server.py file

    # Initialize a new Presentation instance
    prs = Presentation() # slides ratio has to be 16:9 not 4:3

    # Generate here the necessary transformations for generating the PowerPoint presentation according to the user's request. Use titles, subtitles, diagrams, tables, colors, clear fonts, and other elements to make the presentation visually appealing and easy to understand.

    # Save the presentation
    prs.save(PPTX_PATH) # Don not modify this line, it is defined in the server.py file

    # Check if the file was created successfully
    if not os.path.exists(PPTX_PATH):
        raise ValueError(f"Failed to create the PowerPoint file at", PPTX_PATH, "try again")
    else:
        return f"PowerPoint file created successfully!"


# Invoke the function to generate the PowerPoint presentation
power_point()
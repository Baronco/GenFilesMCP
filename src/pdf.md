Generate a PDF with a Python script (`reportlab`). On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_pdf` (`python_script`, `file_name`, `images_list`). For uploaded images, call `fetch_uploaded_chat_file_ids` first; the server preloads them into `LIST_OF_BYTES_IO_IMAGES`.

## Example
```python
def pdf():
    PDF_BUFFER = pdf_buffer            # keep this line exactly
    LIST_OF_BYTES_IO_IMAGES = images   # keep this line exactly (preloaded images)
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(PDF_BUFFER, pagesize=A4)
    story = [Paragraph("Title", styles["Title"]), Spacer(1, 12)]
    # Build the story per the user's request (Paragraph, Table, Image, ...).
    doc.build(story)
pdf()   # keep this call
```

## Rules
- Wrap everything in `def pdf(): ...` and call `pdf()` at the end.
- Keep `PDF_BUFFER = pdf_buffer` exactly (inside the function).
- Use only `reportlab` + the standard library (+ the chart/image libs below).
- Images: take from `LIST_OF_BYTES_IO_IMAGES`, `seek(0)`, wrap in `reportlab.platypus.Image(buf, width=..., height=...)`.
- To add a generated chart: render to a `BytesIO`, `seek(0)`, append to `LIST_OF_BYTES_IO_IMAGES`, wrap in `Image`. Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

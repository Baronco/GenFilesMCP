Generate a PDF with a Python script (`reportlab`). {{SUCCESS_DELIVERY_RULE}}

Call `generate_pdf` (`python_script`, `file_name`, `images_list`). Uploaded images: call `fetch_uploaded_chat_file_ids` first; preloaded into `LIST_OF_BYTES_IO_IMAGES`.

## Example
```python
def pdf():
    PDF_BUFFER = pdf_buffer            # keep this line exactly
    LIST_OF_BYTES_IO_IMAGES = images   # keep this line exactly
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate(PDF_BUFFER, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("Title", styles["Title"]), Spacer(1, 12)]
    # Build story per the request.

    # Chart via seaborn/matplotlib
    import io, seaborn as sns
    from reportlab.platypus import Image as RLImage
    fig = sns.barplot(x=["A","B","C"], y=[10,20,15])
    buf = io.BytesIO(); fig.figure.savefig(buf, format='png', bbox_inches='tight'); buf.seek(0)
    LIST_OF_BYTES_IO_IMAGES.append(buf)
    LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
    story.append(RLImage(LIST_OF_BYTES_IO_IMAGES[-1], width=300, height=200))
    doc.build(story)
pdf()   # keep this call
```

## Rules
- Wrap in `def pdf(): ...`; call `pdf()` at end.
- Keep `PDF_BUFFER = pdf_buffer` exactly (inside function).
- Available: `scipy`, `seaborn`, `matplotlib`, `pillow`, `numpy`.

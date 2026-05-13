Generate a PDF document using a Python script. Returns a markdown hyperlink for downloading the generated file.

Template structure:

```python
# reportlab is the primary package for PDF generation.
# from reportlab.lib.pagesizes import letter, A4
# from reportlab.lib import colors
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch, cm

# Buffer to save the PDF file, previously defined in the server.py file
# IMPORTANT: PDF_BUFFER is a BytesIO buffer (in-memory file-like object), not a file path.
# Writing to it saves in RAM, not on disk.


def pdf():
    PDF_BUFFER = pdf_buffer # Do not modify this line, it is defined in the server.py file

    # If images are needed, they are preloaded by the server and passed here.
    # LIST_OF_BYTES_IO_IMAGES is a list of BytesIO objects.
    LIST_OF_BYTES_IO_IMAGES = images # Do not modify this line if images are needed, it is defined in the server.py file

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    doc = SimpleDocTemplate(
        PDF_BUFFER,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1F3864'),
        spaceAfter=12)
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2E75B6'),
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=8
    )

    story = []
    story.append(Paragraph("Example PDF Doc", title_style))
    story.append(Spacer(1,0.5*cm))
    story.append(Paragraph("Introduction", heading_style))
    story.append(Paragraph(
        "This is an example paragraph. Add your content here following the user's request. "
        "Use titles, headings, tables, and other elements to make the document clear and professional.",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))


    table_data = [
        ["Column A", "Column B", "Column C"],
        ["Row 1 - A", "Row 1 - B", "Row 1 - C"],
        ["Row 2 - A", "Row 2 - B", "Row 2 - C"],
    ]
    table = Table(table_data, colWidths=[5*cm, 5*cm, 5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E75B6')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EAF0FB'), colors.white]),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    doc.build(story)

    return "PDF file created successfully!"
pdf() # It should be always here

```

**Notes:**

- `PDF_BUFFER` is a `BytesIO` object — `SimpleDocTemplate` accepts it directly, no `.encode()` needed.
- Use `reportlab.platypus` flowables (`Paragraph`, `Spacer`, `Table`, `Image`, etc.) to compose the layout.
- For images, use `reportlab.platypus.Image(buffer, width=..., height=...)` where `buffer` is an element from `LIST_OF_BYTES_IO_IMAGES`. Call `.seek(0)` on the buffer before passing it.
- For multi-page documents, flowables automatically paginate — no manual page breaks needed unless you use `PageBreak()`.
- Avoid importing packages outside of `reportlab` and the Python standard library.

> **Reminder:** keep the buffer assignment line `PDF_BUFFER = pdf_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.

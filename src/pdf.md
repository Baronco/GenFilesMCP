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
- Fonts characters:
    - Default fonts (`Helvetica`, `Times-Roman`) only render Latin script (Spanish/English accents, ñ, etc. work fine). They CANNOT render CJK (Japanese/Chinese/Korean), Arabic, Hebrew, Thai, Cyrillic-heavy, or other non-Latin scripts.
    - If the content includes CJK or other non-Latin script, register the matching built-in CID font instead (no external files needed):
    ```python
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))  # Japanese (sans)
    # Also available: 'HeiseiMin-W3' (Japanese serif), 'STSong-Light' (Simplified Chinese),
    # 'MSung-Light' (Traditional Chinese), 'HYSMyeongJo-Medium' (Korean)
    ```
    - Do NOT switch the whole document to the CID font — it's meant for that script only and renders Latin text (spacing, weight) poorly. Keep Spanish/English paragraphs on `Helvetica`/`Helvetica-Bold`, and wrap only the non-Latin fragments with inline font tags in the same `Paragraph`:
    ```python
    Paragraph('Ejemplo: 15日 → <font name="HeiseiKakuGo-W5">じゅうごにち</font> (día 15)', style)
    ```
    - If a table/paragraph is entirely in the non-Latin script (e.g. a full Japanese vocabulary column), it's fine to set that specific `ParagraphStyle`'s `fontName` to the CID font — just don't apply it to the whole document's default styles.
    - These CID fonts have limited weights (often no true bold) — use color/size/underline to create hierarchy instead of relying on bold for non-Latin headers.
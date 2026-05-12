This tool is designed to generate Word documents for reports or academic papers. The input required is a JSON object structured as follows:

- `document_cover`: Metadata for the cover page, including the following fields:
  - `title`: The title of the document.
  - `subtitle`: An optional subtitle for additional context.
  - `description`: A brief description of the document's purpose.
  - `author`: The author's name.
  - `month`: The month of publication (e.g., "January").
  - `year`: The year of publication (e.g., "2024").
  - `page_break`: A boolean indicating whether to start the body content on a new page.
- `columns_body`: Specifies the number of columns in the document body. Acceptable values are `1` or `2`.
- `document_elements`: An ordered list of elements that make up the document body.
- `file_name`: The name of the output file (without the file extension).

### Guidelines for Document Elements:

Each element in the `document_elements` list must include a `type` field with one of the following values:

- `paragraph`: Used for regular paragraphs. Supports inline Markdown emphasis with **bold** and *italic*.
- `header`: Used for section headers.
- `list`: Used for numbered or bulleted lists. Use `style: "bullet"` or `style: "numbered"`.
- `table`: Used for tables.
- `image`: Used for images.
- `equation`: Used for equations.
- `page_break`: Inserts a page break between sections.

The final goal of this tool is to create a well-structured Word document, prioritizing the selection of the best logical order for the document and the correct element types so that the user can obtain a professionally formatted document that is easy to read and ready to be shared or published.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.


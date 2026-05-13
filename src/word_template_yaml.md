Use this tool to createa a Word document from a structured YAML definition.

## YAML structure

Use a raw YAML body with the following top-level keys:

- `cover`: Document cover metadata.
- `columns_body`: Optional number of columns in the body content (`1` or `2`).
- `body`: Ordered YAML list of document elements.

Each element must include a `type` field. Supported element types:
- `header`
- `paragraph`
- `list`
- `table`
- `image`
- `equation`
- `page_break`

## Field details:

- `cover`: Required object with `title`, `subtitle`, `description`, `author`, `month`, `year`, `page_break`.
- `columns_body`: Integer value defining layout columns. If omitted, defaults to `1`.
- `body`: List of ordered elements.

## Element details:

- `header`
  - `text`: Heading text.
  - `level`: Heading level between `1` and `6`.

- `paragraph`
  - `text`: Paragraph content. Supports inline Markdown emphasis with `**bold**` and `*italic*`.

- `list`
  - `style`: `bullet` or `numbered`.
  - `items`: A YAML list of strings.

- `table`
  - `headers`: List of column header strings.
  - `rows`: List of rows, each row is a list of strings.
  - `caption`: Optional table caption.

- `image`
  - `id`: Exact uploaded image file ID.
  - `caption`: Optional caption for the image.

- `equation`
  - `latex`: LaTeX expression (e.g., "E = mc^{2}")
  - `caption`: Optional caption.
  - **Always use pure ASCII LaTeX commands inside `latex` — never substitute Unicode characters for LaTeX symbols.** Write `\hat{y}` not `ŷ`, `\bar{x}` not `x̄`, `\beta` not `β`. Unicode math characters embedded in LaTeX strings corrupt the YAML before the document is built.

- `page_break`
  - No additional fields required.

## Important notes:

- Always use `yaml.safe_load` in the backend parser.
- Do not mix JSON-style objects in the YAML body; use valid YAML syntax.
- Keep image IDs exact and unchanged.
- Use `page_break: true` in the `cover` section to start body content on a new page.

> When generation is successful, the chat UI shows a download button for the generated file. Do not output or mention download links in the assistant response.

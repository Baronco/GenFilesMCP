Generate a Word (.docx) document from a **structured YAML** definition. Returns a markdown hyperlink for downloading the generated file.

Before generating a document that embeds uploaded images, call `fetch_uploaded_chat_file_ids` to get their IDs (pass an exact ID as an `image` element's `id`).

## YAML structure

A document has these top-level keys:

- `style_doc`: Optional document style — `ieee` or `report`. Defaults to `report`.
- `cover`: Document cover metadata (required).
- `body`: Ordered YAML list of document elements.

### `style_doc` — choose the document layout

| value | layout | use it for |
|---|---|---|
| `ieee` | **two columns**, scientific-article look with first-line-indented body paragraphs | academic / scientific papers |
| `report` (default) | **single column**, clean report look with left-aligned headings | informes: analysis, internet-research summaries, idea briefs, drafting help |

- Pick the style with `style_doc`; **you never set the number of columns** — the style decides (ieee = 2, report = 1).
- Omit `style_doc` for a single-column **report** (the default and most common case).
- An unknown value safely falls back to `report`.

Each body element is a flat object with a `type:` field. Supported types: `header`, `paragraph`, `list`, `table`, `image`, `equation`, `page_break`.

## Canonical example (copy this shape)

Every body element is a flat object with a `type:` field — **not** nested under the element name.

```yaml
style_doc: report          # ieee | report (optional, default report)
cover:
  title: "Gradient Descent"
  subtitle: "Foundations"
  description: "A concise report."
  author: "Maru"
  month: "June"
  year: "2026"
  page_break: true
body:
  - type: header
    text: "1. Introduction"
    level: 1
  - type: paragraph
    text: "Body text with **bold** and *italic*."
  - type: list
    style: bullet            # bullet | numbered
    items: ["First point", "Second point"]
  - type: table
    headers: ["Variant", "Speed"]
    rows: [["Batch", "Slow"], ["SGD", "Fast"]]
    caption: "Table 1. Comparison."
  - type: equation
    latex: '\theta := \theta - \alpha \cdot \nabla J(\theta)'   # SINGLE quotes — see equation rules
    caption: "Equation 1. Update rule."
  - type: image
    id: "<uploaded image id>"
    caption: "Figure 1. Diagram."
  - type: page_break
```

> Write `- type: header` (flat), NOT `- header: { ... }` (nested). Keep one element per list item.

## Field details

- `style_doc`: Optional. `ieee` (two-column scientific article) or `report` (single-column report). Defaults to `report`.
- `cover`: Required object with `title`, `subtitle`, `description`, `author`, `month`, `year`, `page_break`.
- `body`: List of ordered elements.

## Element details

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
  - `id`: Exact uploaded image file ID (from `fetch_uploaded_chat_file_ids`).
  - `caption`: Optional caption for the image.

- `equation`
  - `latex`: LaTeX expression, e.g. `'E = mc^{2}'`.
  - `caption`: Optional caption.
  - **Wrap `latex` in SINGLE quotes**, e.g. `latex: '\theta - \alpha \cdot \nabla J(\theta)'`. LaTeX uses backslashes (`\theta`, `\cdot`, `\nabla`, `\frac`); in **double** quotes YAML treats `\t`, `\n`, `\c`, etc. as escape sequences and the document fails to parse. Single quotes keep backslashes literal. (Do **not** double the backslashes.)
  - **Always use pure ASCII LaTeX commands inside `latex` — never substitute Unicode characters for LaTeX symbols.** Write `\hat{y}` not `ŷ`, `\bar{x}` not `x̄`, `\beta` not `β`. Unicode math characters embedded in LaTeX strings corrupt the YAML before the document is built.

- `page_break`
  - No additional fields required.

## Important notes

- Use valid YAML syntax; do not mix JSON-style objects into the body.
- Keep image IDs exact and unchanged.
- Use `page_break: true` in the `cover` section to start body content on a new page.

When generation is successful, the chat UI shows a download button for the generated file. Do not output or mention download links in the assistant response.

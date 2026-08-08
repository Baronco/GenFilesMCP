Generate a Word (.docx) from structured YAML. {{SUCCESS_DELIVERY_RULE}}

Call `generate_word_structured_yaml` (`document_yaml`, `file_name`). For uploaded images call `fetch_uploaded_chat_file_ids` first.

## Inputs
- `cover`: title, subtitle, description, author, month, year, page_break.
- `style_doc`: `ieee`(two-column, indented) | `report`(one-column). Default `report`.
- `body`: flat element list. Types: `header`(text, level 1-6) | `paragraph`(text) | `list`(style bullet|numbered, items) | `table`(headers, rows, caption) | `image`(id, caption) | `equation`(latex, caption) | `page_break`.

## Example
```yaml
style_doc: report
cover: {title: "Title", subtitle: "Sub", description: "Desc.", author: "A", month: "Jun", year: "2026", page_break: true}
body:
  - {type: header, text: "1. Introduction", level: 1}
  - {type: paragraph, text: "Body with **bold** and *italic*."}
  - {type: equation, latex: '\theta := \theta - \alpha', caption: "Eq 1."}
  - {type: image, id: "<file_id>", caption: "Fig 1."}
  - {type: page_break}
```

## Rules
- FLAT: `- {type: header, text: "..."}` — NEVER `- header: {text: "..."}`. One element per item.
- `equation.latex`: SINGLE quotes; ASCII only (`\beta` not β); NO double backslashes.
- `image.id`: exact ID from `fetch_uploaded_chat_file_ids`.
- `cover.page_break: true` starts body on a new page.

Generate a Word (.docx) from structured YAML. On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_word_structured_yaml` (`document_yaml`, `file_name`). For uploaded images, call `fetch_uploaded_chat_file_ids` first.

## Required inputs
- `cover`: object with `title`, `subtitle`, `description`, `author`, `month`, `year`, `page_break`.
- `body`: ordered list of elements; each is a flat object with a `type:`.
- `style_doc` (optional): `ieee` (two-column article, indented body) or `report` (one column). Default `report`.

## Example
```yaml
style_doc: report
cover: {title: "Gradient Descent", subtitle: "Foundations", description: "Short report.", author: "Maru", month: "June", year: "2026", page_break: true}
body:
  - {type: header, text: "1. Introduction", level: 1}
  - {type: paragraph, text: "Body with **bold** and *italic*."}
  - {type: list, style: bullet, items: ["First", "Second"]}
  - {type: table, headers: ["A", "B"], rows: [["1", "2"]], caption: "Table 1."}
  - {type: equation, latex: '\theta := \theta - \alpha \cdot \nabla J(\theta)', caption: "Eq 1."}
  - {type: image, id: "<file_id>", caption: "Figure 1."}
  - {type: page_break}
```

## Rules
- Write each element FLAT with `type:` — never nested (`- type: header`, not `- header:`). One element per list item.
- `style_doc` decides the columns; never set columns yourself. Unknown value → `report`.
- Element fields: `header` (text, level 1-6); `paragraph` (text, supports `**bold**`/`*italic*`); `list` (style `bullet`|`numbered`, items); `table` (headers, rows, caption); `image` (id, caption); `equation` (latex, caption); `page_break`.
- `equation.latex`: wrap in SINGLE quotes; ASCII only (`\beta`, not β); do NOT double the backslashes.
- `image.id`: exact ID from `fetch_uploaded_chat_file_ids`.
- `cover.page_break: true` starts the body on a new page.

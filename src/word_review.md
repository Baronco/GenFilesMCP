Review an uploaded Word (.docx) with inline comments.

## Call chain
1. `fetch_uploaded_chat_file_ids` → `file_id`
2. `list_docx_elements(file_id, file_name)` → element list (each row has `index` + text)
3. `review_docx(file_id, file_name, review_comments)` ← `index` values from step 2

## review_comments
List of `{"index": int, "comment": str}`:
```json
[{"index": 0, "comment": "Typo: 'teh' → 'the'"}, {"index": 5, "comment": "Unclear; split this sentence."}]
```

## Rules
- `index` MUST come from step 2 — NEVER guess.
- Keep comments specific and actionable.
- On success the chat shows a download button — never invent a download link.

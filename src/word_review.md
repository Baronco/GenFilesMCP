Review an uploaded Word (.docx) by adding comments (spelling, grammar, style, clarity). Two steps.

## Steps
1. Get the `file_id`: call `fetch_uploaded_chat_file_ids`.
2. `list_docx_elements` (`file_id`, `file_name`) → returns each element's `index`, style, and text.
3. `review_docx` (`file_id`, `file_name`, `review_comments`) → adds the comments.

## review_comments
A list of `{"index": int, "comment": str}`:
```json
[{"index": 0, "comment": "Typo: 'teh' -> 'the'"}, {"index": 5, "comment": "Unclear; split this sentence."}]
```

## Rules
- `index` must come from `list_docx_elements` for the SAME document.
- Comment only where it helps; keep each comment specific and actionable.
- On success the chat shows a download button for the reviewed file automatically — never write or invent a download link.

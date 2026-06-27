Review an existing Word (.docx) document by adding targeted comments (spelling, grammar, style, clarity). This is a **two-step workflow** over a document the user uploaded in the chat.

**Step 0 — get the document's file ID:** call `fetch_uploaded_chat_file_ids` to obtain the uploaded `.docx` `file_id` and its original name. The `file_id` is the value you pass to the review tools below.

**Step 1 — inspect the structure (`list_docx_elements`):** call with `file_id` and `file_name`. It returns each element's **index**, style, and text. Use the indexes to decide which elements to comment on.

**Step 2 — add comments (`review_docx`):** call with `file_id`, `file_name`, and `review_comments` = a list of `{"index": <int>, "comment": <str>}` objects, where `index` is an element index from Step 1. Example:

```json
[{"index": 0, "comment": "Fix typo: 'teh' -> 'the'"},
 {"index": 5, "comment": "This sentence is unclear; consider splitting it."}]
```

- Only comment where it genuinely improves the document; keep each comment specific and actionable.
- `index` must come from the `list_docx_elements` output for the **same** document.
- When the review is saved, the chat UI shows a download button for the reviewed file.

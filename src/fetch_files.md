Fetch the IDs of files and images the user uploaded in the current chat. Returns a list of `file_id` values for the attachments found in the conversation.

**Call this FIRST** whenever a request involves an uploaded file or image — then use the returned `file_id` as the input the other tools need:

- **Embed an image in a generated file** — pass the `file_id` as:
  - `image_id` on a slide (PowerPoint YAML), or `id` on an `image` element (Word YAML);
  - an entry of `images_list` (PowerPoint / Word / PDF **Python** modes).
  The server downloads the image by that ID and places it in the document.
- **Review an uploaded Word document** — pass the `file_id` to `list_docx_elements` and `review_docx` to inspect the document and add comments.

Notes:
- The `file_id` is the only handle to an uploaded file — **use it exactly as returned**, never invent or modify it.
- If the request needs an uploaded image/file but no IDs come back, ask the user to attach the file in the chat.
- Excel and Markdown generation do not embed binary images, so they rarely need this.

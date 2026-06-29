Return the `file_id` of each file/image the user uploaded in the current chat.

Call `fetch_uploaded_chat_file_ids` FIRST whenever a request involves an uploaded file or image.

## Use the returned file_id
- Embed an image: as `image_id` (PowerPoint YAML), `id` on an `image` element (Word YAML), or an entry of `images_list` (Python modes).
- Review a Word doc: as `file_id` for `list_docx_elements` and `review_docx`.

## Rules
- Use the `file_id` exactly as returned; never invent or change it.
- If an upload is needed but no IDs come back, ask the user to attach the file.
- Excel and Markdown cannot embed binary images.

Return `file_id` for each uploaded file/image. Call FIRST on any request involving uploads.

Use as: `image_id`(PPTX YAML) | `id` on `image` element(Word YAML) | `images_list` entry(Python modes) | `file_id` for `list_docx_elements`/`review_docx`.

## Rules
- Use `file_id` exactly as returned — NEVER invent or modify it.
- No IDs returned → ask user to attach the file.
- Excel and Markdown CANNOT embed binary images.

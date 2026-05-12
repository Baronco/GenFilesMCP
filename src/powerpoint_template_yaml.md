Use this tool to create a PowerPoint presentation from a structured YAML definition.

## YAML structure

- `global`: presentation-wide settings
  - `accent_color`: hex color used for accent areas
  - `background_color`: hex color used for slide backgrounds
  - `font_heading`: font name for slide headings
  - `font_body`: font name for paragraph text
- `slides`: ordered list of slide objects
  - each slide must include a `type` field

## Supported slide types

- `cover`
- `section_divider`
- `content_image`
- `content_text`
- `content_latex`
- `two_column`
- `content_mixed`

> **LaTeX equations are only rendered in `content_latex` slides.** In all other slide types (`content_text`, `content_image`, `two_column`, `content_mixed`, etc.) the text is inserted as plain text — any LaTeX syntax like `$\frac{1}{2}$` or `\mathbb{R}` will appear literally on the slide with all its special characters. If a slide needs mathematical notation, use `content_latex`.

## Slide field reference

### cover
- `title` (required): the main presentation title; can include a leading emoji to reinforce the topic visually
- `subtitle` (optional)
- `date` (optional)
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

### section_divider
- `title` (required): chapter or section name; can include a leading emoji to mark the section visually
- `subtitle` (optional)
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

### content_image
- `header_bar` (optional, true/false, default: true): renders an accent-colored bar at the top with the slide title. Set to false only when a full-bleed background or custom layout is needed.
- `title` (required)
- `text` (required)
- `image_id` (required)
- `background` (optional): `accent_color`, `background_color`, or a hex color like `#1E3A5F`. Text color is chosen automatically for contrast.
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

### content_text
- `header_bar` (optional, true/false, default: true): renders an accent-colored bar at the top with the slide title. Set to false only when a full-bleed background or custom layout is needed.
- `title` (required)
- `text` (required): full slide body text, supports long paragraphs
- `background` (optional): `accent_color`, `background_color`, or a hex color like `#1E3A5F`. Text color is chosen automatically for contrast.
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

> Use `content_text` when the slide only needs a title and body text with no images, charts, or tables.

### two_column
- `title` (required)
- `left` (required): object with `title` and `text`
- `right` (required): object with `title` and `text`
- `background` (optional): `accent_color`, `background_color`, or a hex color like `#1E3A5F`. Text color is chosen automatically for contrast.
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

> Important: use nested `left:` and `right:` objects. Do not use `left_title`, `left_text`, `right_title` or `right_text`.

### content_latex
- `header_bar` (optional, true/false, default: true): renders an accent-colored bar at the top with the slide title. Set to false only when a full-bleed background or custom layout is needed.
- `title` (required)
- `text` (optional): brief description shown above the rendered equation block
- `latex_lines` (required): ordered list of mathtext strings rendered as a stacked image
  - wrap equations in `$...$`, e.g. `$E = mc^2$`
  - use `$\bullet\;$` prefix for bullet-style items: `$\bullet\;$ Step 1: $F = ma$`
  - mix text and math freely: `Kinetic energy: $E_k = \frac{1}{2}mv^2$`
  - **Always use single-quoted strings (`'...'`) for `latex_lines` items that contain backslashes** — YAML double-quoted strings interpret `\` as an escape character and will fail on `\mathbb`, `\frac`, `\alpha`, etc.
- `background` (optional): `accent_color`, `background_color`, or a hex color like `#1E3A5F`. Text color is chosen automatically for contrast.
- `notes` (optional): brief presenter notes

> Use `content_latex` when the slide needs to display mathematical equations, derivation steps, or any content that requires LaTeX math formatting. Equations are rendered via matplotlib mathtext — no external LaTeX installation needed.

### content_mixed
- `header_bar` (optional, true/false, default: true): renders an accent-colored bar at the top with the slide title. Set to false only when a full-bleed background or custom layout is needed.
- `title` (required)
- `text` (optional)
- exactly one of:
  - `image_id`
  - `chart`
  - `table`
- `background` (optional): `accent_color`, `background_color`, or a hex color like `#1E3A5F`. Text color is chosen automatically for contrast.
- `notes` (optional): brief presenter notes — concise cues or clarifications visible only to the speaker, not shown on the slide

> Important: `content_mixed` must include exactly one of `image_id`, `chart`, or `table`.

## Images

For slides with images, use `image_id` values inside the YAML. The server automatically extracts these IDs and downloads image data into memory. You do not need to pass a separate `images_list`.

Use `/fetch_uploaded_chat_file_ids` first to get the valid image IDs that are available in the current chat.

## YAML quoting rules

Backslashes in LaTeX (`\mathbb`, `\frac`, `\alpha`, etc.) break YAML double-quoted strings because `\` is treated as an escape character. Follow these rules:

- Use **single quotes** for any string containing backslashes: `subtitle: 'Least squares in $\mathbb{R}^2$'`
- Use **single quotes** for all `latex_lines` items: `- '$E_k = \frac{1}{2}mv^2$'`
- If the string itself contains a single quote, escape it by doubling it: `'it'\''s fine'` → `'it''s fine'`
- Plain (unquoted) strings are safe only when they contain no backslashes or special YAML characters
- **Always use pure ASCII LaTeX commands — never substitute Unicode characters for LaTeX symbols.** Write `\hat{y}` not `ŷ`, `\bar{x}` not `x̄`, `\alpha` not `α`. Unicode math characters inside LaTeX strings corrupt the YAML before the presentation is built.

## Common validation issues

- Missing `left` or `right` object inside a `two_column` slide
- Using `left_title` / `left_text` / `right_title` / `right_text` instead of nested objects
- `content_mixed` without `image_id`, `chart`, or `table`
- More than one of `image_id`, `chart`, `table` in a `content_mixed` slide
- Invalid `background` value. Use theme-aware colors like `accent_color` or `background_color`, or provide an explicit color for the document theme. Ensure there is good contrast between background and text.
- Using `content_mixed` with only text — use `content_text` instead
- Using double-quoted strings for values that contain LaTeX backslashes — use single quotes instead

> When generation is successful, the chat UI shows a download button for the generated file. Do not output or mention download links in the assistant response.

> **If the user cannot open or download a generated document** from the chat, ask them to enable **Settings → Interface → Artifacts → iframe Sandbox Allow Same Origin** (toggle on). This Open WebUI option is required for document download links inside the chat iframe to work correctly.
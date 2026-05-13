Generate a PowerPoint from YAML. Top-level keys: `global` and `slides`.

## global (required)
```yaml
global:
  accent_color: "#0D9488"   # options: "#0D9488" | "#6D28D9" | "#E05C3A" | "#059669" | "#1E293B" | "#334155" | "#0F4C81"
  background_color: "#F0FDFA"   # options: "#F0FDFA" | "#FAF5FF" | "#FFF7F5" | "#F0FDF4" | "#F1F5F9" | "#F8FAFC" | "#F7F9FC"
  font_heading: Calibri
  font_body: Calibri
```
**Pair accent and background by position (same index = one palette). Never default to `#1F6AA5`.**

## Slide types and fields

| type | required fields | optional fields |
|---|---|---|
| `cover` | `title` | `subtitle`, `date`, `notes` |
| `section_divider` | `title` | `subtitle`, `notes` |
| `content_text` | `title`, `text` | `header_bar`, `background`, `notes` |
| `content_image` | `title`, `text`, `image_id` | `header_bar`, `background`, `notes` |
| `two_column` | `title`, `left{title,text}`, `right{title,text}` | `background`, `notes` |
| `content_mixed` | `title` + exactly one of `image_id`/`chart`/`table` | `text`, `header_bar`, `background`, `notes` |
| `content_latex` | `title`, `latex_lines` | `layout`, `text`, `header_bar`, `background`, `notes` |

- `header_bar` (default `true`): accent-colored title bar at top.
- `background`: `accent_color`, `background_color`, or explicit hex `#RRGGBB`.
- `two_column`: use nested `left:` / `right:` objects — never `left_title`, `right_text`, etc.
- `content_mixed`: exactly **one** of `image_id`, `chart`, `table`. Text-only → use `content_text`.
- `content_latex` `layout`: `"split"` (default — text on left, equations image on right; requires `text`) or `"full"` (equations fill the entire slide).

## Chart types (for `content_mixed chart:`)
| type | required fields | optional | description |
|---|---|---|---|
| `bar` | `categories`, `values` | `title` | Column bar chart |
| `line` | `categories`, `values` | `title` | Line chart with area fill |
| `pie` | `categories`, `values` | `title` | Pie chart |
| `scatter` | `x`, `y` | `title` | Scatter plot |
| `histogram` | `values` | `title`, `bins` | Histogram (default 10 bins) |
| `boxplot` | `series`, `categories` | `title` | Box plot; `series` is a list of value lists (one per box) |

## Emojis in titles
**Always add a relevant emoji at the start of every `title` field** (all slide types including `cover`, `section_divider`, column titles, etc.). Emojis provide quick visual cues and make the deck more engaging.
Examples: `📉 Gradient Descent`, `⚙️ Algorithm Variants`, `📊 Comparison of Types`, `🔢 The Mathematics`, `⚠️ Common Pitfalls`.

## Text formatting (non-latex slides)
Body text supports inline markdown: `**bold**`, `*italic*`, `***bold+italic***`, `` `code` ``, bullet lists (`- item`), numbered lists (`1. item`).

**Never use LaTeX (`$...$`, `\frac`, `\alpha`) outside `content_latex`.** It will appear as raw symbols and garbled text. For any equation or math notation, always use `content_latex`.
**Never write markdown tables in `text` fields.** Pipe-table syntax (` | col | `) is auto-parsed and rendered as a PPTX table, but the result may be poorly positioned. For tables, always use `content_mixed` with a `table:` block.

## content_latex — latex_lines
List of mathtext strings rendered as an image via matplotlib:
- Wrap math in `$...$`: `'$E = mc^2$'`
- Bullets: `'$\bullet\;$ Step 1'`
- **Always single-quote** strings with backslashes — double quotes break YAML on `\frac`, `\alpha`, etc.
- Use ASCII LaTeX only: `\hat{y}` not `ŷ`, `\alpha` not `α`.
- For a split layout (context text + equations side-by-side): set `layout: split` and provide `text`.

## Images
Use `image_id` values from `/fetch_uploaded_chat_file_ids`. The server fetches them automatically — no `images_list` needed.

> On success the UI shows a download button. Do not mention download links in the response.
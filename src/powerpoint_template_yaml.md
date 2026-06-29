Generate a PowerPoint (.pptx) from structured YAML (one theme + a list of slides). On success the chat shows a download button automatically — never write or invent a download link.

Call `generate_powerpoint_structured_yaml` (`document_yaml`, `file_name`). For uploaded images, call `fetch_uploaded_chat_file_ids` first and use the ID as a slide `image_id`.

## Required inputs
- `theme`: one theme name for the whole deck.
- `slides`: ordered list; each slide has a `type`.

## Example
```yaml
theme: corporate_blue
slides:
  - {type: cover, title: "🚀 Title", subtitle: "...", date: "May 2026"}
  - {type: section_divider, title: "📌 Section"}
  - {type: content_text, title: "📝 Slide", text: "Line 1\nLine 2"}
  - {type: two_column, title: "⚖️ Compare", left: {title: "A", text: "- x\n- y"}, right: {title: "B", text: "- x\n- y"}}
  - type: content_mixed          # one visual only: chart | table | image_id
    title: "📊 Chart"
    chart: {intent: comparison, categories: ["A", "B"], values: [10, 20]}
  - type: content_latex
    title: "📐 Math"
    latex_lines: ['$y = \beta_0 + \beta_1 x$', '$\frac{dy}{dx} = \beta_1$']
  - type: timeline
    title: "📅 Milestones"
    style: horizontal            # horizontal | vertical
    active_index: 1
    items: [{fecha: "Jan 2024", titulo: "Kickoff"}, {fecha: "Mar 2024", titulo: "Design"}]
  - {type: stat_highlight, value: "40%", label: "YoY growth", supporting_text: "..."}
```

## Slide types
cover, section_divider, content_text, content_image, two_column, content_mixed, content_latex, timeline, stat_highlight.
- `content_text.text`: a string with `\n`; lines starting `- `/`* `/`1.` become bullets. Never a YAML list.
- `content_mixed`: `text` on the left + exactly ONE of `chart` | `table` | `image_id` on the right.
- `timeline`: a roadmap/agenda of the topics the deck covers — ≥2 items `{fecha, titulo}`; `style` horizontal (3-5) | vertical (4-6/long titles); `active_index` highlights one; vertical may add `image_id` or `text`.
- `stat_highlight`: one big number; use 1-2 per deck.

## Theme
Pick ONE; unknown/missing → `corporate_blue`. Each is one soft, WCAG-safe color family:
corporate_blue, warm_editorial, minimal_mono, vibrant_teal, royal_purple, crimson_report, forest_green, amber_gold, modern_dark, emerald_dark, graphite_dark.

## Math — use `content_latex` only
LaTeX written in a `text` field (content_text, content_mixed, two_column, …) is NOT rendered — it appears as raw, unformatted text. Put EVERY formula in a `content_latex` slide via `latex_lines`; never as plain text or Unicode in other slides.
- Each line in single `$...$`. Bold `\mathbf{}` (never `\textbf`). Balanced braces. ASCII only (`\beta`, not β). No `\begin{...}` environments and no `\displaystyle`/`\dfrac` (use `\frac`).
- `layout: full` (default) or `split` (needs `text` or `image_id`).

## Charts
Pick one `intent` + its data; the theme palette is applied automatically.
- `intent` is ONE of the four below. Shape names (scatter, bar, pie, line, …) go in `chart_type`, NEVER in `intent`.
- `comparison`: categories + values. `trend`: x + y. `distribution`: values. `part_of_whole`: categories + values.
- Optional: `title`, `x_label`, `y_label`, `value_format` (auto|int|float1|percent|thousands|currency), `value_labels`, `legend`.
- Single-series bars auto-sort high→low — do NOT pre-sort.
- Multiple series: `series: [{name, values}]` sharing the same `categories`/`x` (series replaces only the y-values, not the axis).
- Optional `chart_type`: bar, stacked_bar, stacked_bar_100, line, area, stacked_area, pie, doughnut, scatter, bubble, combo, waterfall. Unknown → intent default.
- `combo`: each series sets `kind` (bar|line|area) and `axis` (primary|secondary); add `y2_label`.
- `image_id`: exact ID from `fetch_uploaded_chat_file_ids`.

## style_override (rare)
Only to make a title minimal: `style_override: {header_bar: false}`. `header_bar` true (default) = accent tab; false = title only. `background` is ignored. Does not apply to cover/section_divider/stat_highlight.

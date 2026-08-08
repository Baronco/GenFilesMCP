Generate a PowerPoint (.pptx) from structured YAML (theme + ordered slides). {{SUCCESS_DELIVERY_RULE}}

Call `generate_powerpoint_structured_yaml` (`document_yaml`, `file_name`). `theme`: one name. `slides`: ordered list; each has a `type`. For uploaded images call `fetch_uploaded_chat_file_ids` first; use the ID as `image_id`.

## Example
```yaml
theme: corporate_blue
slides:
  - {type: cover, title: "🚀 Title", subtitle: "...", date: "May 2026"}
  - {type: content_text, title: "📝 Text", text: "Line 1\nLine 2"}
  - {type: content_mixed, title: "📊 Mixed", chart: {intent: comparison, categories: ["A","B"], values: [10,20]}}
  - {type: content_latex, title: "📐 Math", latex_lines: ['$y = \beta_0 + \beta_1 x$']}
  - {type: timeline, title: "📅 Roadmap", style: horizontal, active_index: 1, items: [{fecha: "Jan", titulo: "Start"}, {fecha: "Mar", titulo: "Done"}]}
  - {type: stat_highlight, value: "40%", label: "YoY growth", supporting_text: "..."}
```

## Slide types
`cover|section_divider|content_text|content_image|two_column|content_mixed|content_latex|timeline|stat_highlight`
- `cover` and `section_divider` render white title/subtitle text and a white accent bar on a colored gradient background for strong contrast.
- `text` field: `\n`= line break; `- `/`* `/`1.` prefix→bullet. NEVER a YAML list.
- `content_mixed`: optional `text` left + ONE of `chart`|`table`|`image_id` right.
- `timeline`: ≥2 `{fecha,titulo}` items; `style` horizontal(3-5)|vertical(4-6); `active_index` marks active.
- `stat_highlight`: one KPI number; max 2/deck.

## Theme
Pick ONE (unknown→`corporate_blue`):
`corporate_blue|warm_editorial|minimal_mono|vibrant_teal|royal_purple|crimson_report|forest_green|amber_gold|modern_dark|emerald_dark|graphite_dark`

## Math
ONLY `content_latex` renders formulas — LaTeX in other `text` fields appears as raw text.
Each line: single `$...$` | ASCII only (`\beta` not β) | `\mathbf{}` bold | `\frac` not `\dfrac` | no `\begin{...}` | balanced braces.
`layout: full`(default) | `split`(needs `text` or `image_id`).

## Charts
`intent`: `comparison`(categories+values) | `trend`(x+y) | `distribution`(values) | `part_of_whole`(categories+values). NEVER put shape names in `intent`.
- Optional: `title`, `x_label`, `y_label`, `value_format`(auto|int|float1|percent|thousands|currency), `value_labels`, `legend`.
- `chart_type`: bar|stacked_bar|stacked_bar_100|line|area|stacked_area|pie|doughnut|scatter|bubble|combo|waterfall. Unknown→intent default.
- Single-series bars auto-sort high→low — NEVER pre-sort. Multi-series: `series:[{name,values}]` shared `categories`/`x`.
- `combo`: `kind`(bar|line|area) + `axis`(primary|secondary) per series; add `y2_label`.

## style_override
`{header_bar:false}` removes accent tab (default true). Not valid on cover|section_divider|stat_highlight.

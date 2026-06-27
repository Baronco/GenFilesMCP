---
name: powerpoint-generation
description: Generate a PowerPoint (.pptx) presentation — structured YAML generation from a theme plus slide definitions, or Python-script generation.
---

# PowerPoint (.pptx) generation

Use this skill whenever the user wants a slide deck. Pick a mode below; prefer YAML for clean, theme-consistent decks.

**Before generating** a deck that embeds uploaded images, call `fetch_uploaded_chat_file_ids`: pass an exact ID as `image_id` on a slide (YAML) or as `images_list` (Python).

> ⚠️ **Formulas / equations → use the `content_latex` slide type.** Any slide that involves math (equations, fractions, summations, integrals, Greek letters, sub/superscripts, norms, etc.) MUST be a `content_latex` slide using `latex_lines`. Never write formulas as plain `text` on `content_text`, `content_mixed`, `two_column`, or other slide types, and never paste Unicode math symbols (e.g. β, √, ≤, ∑, ŷ) into text fields — only `content_latex` renders math, and only from valid LaTeX/mathtext.

### `latex_lines` — rules to avoid blank/garbled equations

Each entry in `latex_lines` is rendered by matplotlib **mathtext** (NOT full LaTeX). Invalid mathtext degrades a line to plain text and can look wrong, so:

- **Wrap each line in single `$...$`** (e.g. `'$E = mc^2$'`). Do not use `$$...$$` display delimiters.
- **For bold use `\mathbf{...}`, for italic `\mathit{...}` — NEVER `\textbf{...}` or `\textit{...}`** (those are unsupported and break the line). For upright words use `\text{...}`.
- **Keep every brace balanced.** A stray `}` (e.g. `$\text{+} fast}$`) breaks the whole line. Write `$\mathbf{+ fast}$` or `$\text{+ fast}$`.
- **Don't mix plain prose outside math mode**; put descriptive words inside `\text{...}`. Put narrative sentences in the slide's `text:` field instead, not in `latex_lines`.
- **No unsupported constructs**: avoid `\begin{...}` environments (e.g. `bmatrix`), `\textbf/\textit`, custom sizing (`\big`,`\Big`). Supported: `\frac`, `\sqrt`, `\sum`, `\int`, `\nabla`, `\partial`, `\mathbb{}`, `\mathbf{}`, `\text{}`, `\left( \right)`, Greek (`\alpha`,`\theta`,…), `\to`,`\Rightarrow`,`\leq`,`\geq`,`\approx`, sub/superscripts `_{}` `^{}`.
- **ASCII only inside math** — write `\beta` not `β`, `\leq` not `≤`, `\nabla` not `∇`.

**Which tool to call**
- YAML generation → `generate_powerpoint_structured_yaml` (`document_yaml`, `file_name`).
- Python generation → `generate_powerpoint` (`python_script`, `file_name`, `images_list`).

---

## Mode 1 — YAML structured generation

Use this tool to create a PowerPoint presentation from a structured YAML definition.

A presentation has exactly two top-level keys: `theme` (one named style for the whole deck)
and `slides` (an ordered list). There is no per-slide background, header bar, or text-style
field to decide — every slide looks professional from the theme alone. Use `style_override`
only on the rare slide that needs the more minimal title (`header_bar: false`).

## Canonical example

```yaml
theme: corporate_blue   # see "Themes" below — pick ONE for the whole deck
slides:
  - type: cover
    title: "🚀 Title"        # always start titles with emoji
    subtitle: "..."
    date: "May 2026"
  - type: section_divider
    title: "📌 Section"
  - type: content_text
    title: "📝 Slide"
    text: "Line 1\nLine 2"   # text = string + \n, NEVER a yaml list
                              # lines starting with "- ", "* ", "•" or "1." render as bullets automatically
  - type: two_column
    title: "⚖️ Compare"
    left:  {title: "A", text: "- x\n- y"}
    right: {title: "B", text: "- x\n- y"}
  - type: content_mixed        # exactly one of: chart | table | image_id
    title: "📊 Chart"
    text: "optional left text"
    chart:
      intent: comparison       # comparison | trend | distribution | part_of_whole — see "Charts" below
      categories: ["A", "B"]
      values: [10, 20]
  - type: content_mixed
    title: "📋 Table"
    text: "Summary text on the left"
    table:
      headers: ["Col1", "Col2"]
      rows: [["a","1"], ["b","2"]]  # all values strings
  - type: content_latex  # Use content_latex for formulas and equations; other slide types are not designed to render LaTeX.
    title: "📐 Math"
    latex_lines: # Each line here must be valid LaTeX; invalid lines can cause rendering to fail.
      # - The backend wraps missing math in $...$, but the line must still be valid mathtext.
      # - Use \text{...} for any accompanying plain text inside a math expression.
      # - Do not mix plain text outside of math mode in latex_lines.
      # - Use \|...\| for norms and valid LaTeX delimiters.
      # - Avoid environments like \begin{bmatrix} or unsupported matrix syntax.
      - '$\text{Step 1: define the line model } y = \beta_0 + \beta_1 x$'
      - '$\text{Step 2: compute the derivative } \frac{dy}{dx} = \beta_1$'
      - '$\text{Where } y = \beta_0 + \beta_1 x$'
    layout: full   # full | split (split needs text: OR image_id:)
    text: "Optional prose (no LaTeX here)"
    # image_id: img_1   # split only: equations on the LEFT, a normal image on the RIGHT
                         # (takes priority over text: if both are set)
  - type: timeline
    title: "📅 Milestones"
    style: horizontal         # horizontal (axis across slide, 3-5 events) | vertical (top-down rail, 4-6 events / longer titles)
    active_index: 1           # 0-based, highlights one item
    # image_id: img_1         # vertical only: image on the LEFT, rail shifts right
    # text: "Intro paragraph" # vertical only: text on the LEFT instead of an image
    items:
      - {fecha: "Jan 2024", titulo: "Kickoff"}
      - {fecha: "Mar 2024", titulo: "Design"}
  - type: stat_highlight       # spotlight ONE key figure — use sparingly, 1-2 per deck max
    value: "40%"
    label: "Year-over-year growth"
    supporting_text: "Optional one-line context"
```

> `content_mixed` puts `text` on the left, chart/table/image on the right. Omit `text` to leave left side empty.
> `content_latex` with `layout: split` pairs the equations image with either `text` or
> `image_id`. With `text`: prose on the LEFT, equations on the RIGHT. With `image_id`:
> equations on the LEFT, the normal photo/diagram on the RIGHT. If both are set, `image_id`
> takes priority.
> `timeline` requires ≥2 items. `fecha`, `titulo` are strings; `emoji` is optional (markers
> are clean dots — emoji are no longer drawn inside them). `style` defaults to `horizontal`;
> use `vertical` for 4-6 events or longer titles. In `vertical` style you may add `image_id`
> or `text` to fill the left half (the rail then moves to the right) — great for pairing a
> photo or short intro with the chronology.
> `stat_highlight` is for the one number that should land hard (e.g. a headline growth metric).
> It renders on the normal light content background with the figure inside a bold colored KPI
> card — so it stands out as a highlight WITHIN the current section, without looking like a
> `section_divider` (which opens a new section). Don't overuse it; it dilutes the "moment."

## Themes

Pick exactly one `theme` for the whole presentation. Every slide automatically uses that
theme's colors, fonts, and chart palette — there is nothing else to configure. Each theme is
generated from a single base hue, so its backgrounds, accents, impact gradients, and chart
colors all stay in one coherent color family (a blue theme stays blue throughout — never a
mix of unrelated tones).

Pick a theme whose color fits the topic — don't default to blue every time. All themes use a
light (near-white) background with a colored accent; tones are kept soft, not glaring. Every
theme's color pairings (text on background, titles on header bars, impact-slide titles on the
gradient) are verified to meet WCAG contrast minimums, so any theme is safe to use.

| theme | look |
|---|---|
| `corporate_blue` (default) | Clean blue on a light background. Safe default for business decks. |
| `warm_editorial` | Warm orange-red on near-white. Narrative/editorial content. |
| `minimal_mono` | Muted slate-gray on near-white. Understated, minimal look. |
| `vibrant_teal` | Green-teal on near-white. Growth/impact stories. |
| `royal_purple` | Purple on near-white. Creative/premium content. |
| `crimson_report` | Red on near-white. Bold, serious reports/alerts. |
| `forest_green` | Natural green on near-white. Sustainability/health/finance. |
| `amber_gold` | Amber-gold on near-white. Awards, premium, retrospectives. |
| `modern_dark` | Blue on near-white, tech feel. (Light background despite the name.) |
| `emerald_dark` | Emerald green on near-white. Tech with a green identity. |
| `graphite_dark` | Cool steel-gray on near-white. Sleek, neutral. |

If you omit `theme` or misspell it, the tool falls back to `corporate_blue` automatically —
it never fails the request over an unrecognized theme name.

`cover`, `section_divider`, and `stat_highlight` automatically render with an eye-catching
gradient background and a subtle decorative accent (derived from the theme — nothing to
configure). Every other slide type stays flat and clean so body content remains easy to read.

## Charts: intents + optional refinements

Every chart picks ONE `intent`. By default the tool renders a sensible chart with the
active theme's palette automatically — there is no `palette` field to set.

| intent | use it for | required fields |
|---|---|---|
| `comparison` | comparing values across categories | `categories` (strings) + `values` (numbers), same length |
| `trend` | a value changing over time/sequence | `x` (numbers) + `y` (numbers), same length |
| `distribution` | how a single set of values is spread out | `values` (numbers) |
| `part_of_whole` | shares of a total | `categories` (strings) + `values` (numbers), same length |

`title` is optional on any chart. Everything below is **optional** — an intent + its
data alone still works exactly as before.

> **Always provide the axis labels.** `comparison`/`part_of_whole` need `categories`;
> `trend` needs an axis too — use `x` (numbers) for a numeric axis, or `categories`
> (strings) for a labeled axis like days/months. When you use `series` (below), the
> axis stays the SAME field — `series` only replaces the y-`values`, it does **not**
> replace `categories`/`x`.

**Presentation polish** (great for exec decks): `x_label`, `y_label` (axis names),
`value_format` (`auto`|`int`|`float1`|`percent`|`thousands`|`currency`),
`value_labels` (true/false — bars show their value on top by default),
`legend` (true/false).

> Single-series **bar** charts are automatically sorted **highest → lowest** (a ranking) by
> the backend — you don't need to pre-sort the data. (Trend lines, waterfalls, and
> multi-series charts keep the order you provide.)

**Multiple series** — pass `series` (a list of `{name, values}`) instead of a single
`values`, sharing the same `categories` (or `x`). Keep the axis field — each series is
just its y-values. Drives grouped/stacked/multi-line/combo. Example (grouped bars):
```yaml
chart:
  intent: comparison
  chart_type: bar            # or stacked_bar / stacked_bar_100
  categories: ["Q1","Q2","Q3","Q4"]   # the shared axis — still required
  y_label: "Unidades"
  series:
    - { name: "Producto A", values: [120,140,160,180] }
    - { name: "Producto B", values: [90,95,100,130] }
```

**Explicit chart_type** (optional) — name a specific shape:
`bar`, `stacked_bar`, `stacked_bar_100`, `line`, `area`, `stacked_area`,
`pie`, `doughnut`, `scatter`, `bubble`, `combo`, `waterfall`.
Omit it to use the intent's default. An unknown value safely falls back.

For `combo`, each series can set `kind` (`bar`/`line`/`area`) and `axis`
(`primary`/`secondary`), with `y2_label` naming the secondary axis.

Example — combo (revenue bars + margin line on a second axis):
```yaml
chart:
  intent: comparison
  chart_type: combo
  categories: ["Q1","Q2","Q3","Q4"]
  y_label: "Ingresos (M$)"
  y2_label: "Margen %"
  series:
    - { name: "Ingresos", values: [1.2,1.4,1.6,1.8], kind: bar,  axis: primary }
    - { name: "Margen %", values: [22,24,27,29],      kind: line, axis: secondary }
```

## Optional: style_override (advanced — most slides don't need this)

Only add `style_override` to a slide that needs the minimal title style. The only field that
has an effect is `header_bar`:

```yaml
- type: content_text
  title: "Slide with a minimal title"
  text: "..."
  style_override:
    header_bar: false       # true (default) = accent tab + title + rule; false = title + rule only
```

- `header_bar: true` (default) renders the title with a small accent tab; `header_bar: false`
  drops the tab for an even more minimal title. Both keep the clean theme look.
- **`background` is deprecated and ignored.** Custom per-slide backgrounds were removed so the
  whole deck stays cohesive (light, on-theme). It is still accepted in YAML (old decks don't
  break) but has no visual effect. To make a slide stand out as a "moment", use a `cover`,
  `section_divider`, or `stat_highlight` slide instead — those are the theme's built-in,
  harmonized impact slides.

`header_bar` is available on: `content_text`, `content_image`, `content_mixed`,
`content_latex`, `two_column`, `timeline`. It does not apply to `cover` / `section_divider` /
`stat_highlight` (they have their own fixed layouts).

---

## Mode 2 — Python-script generation

Generate a PowerPoint presentation using a Python script. Returns a markdown hyperlink for downloading the generated file.

Template structure:
```python
# Allowed packages
import numpy as np
from pptx import Presentation
from pptx.util import Inches, Pt

# Import here other pptx packages you need, but do not import other packages that are not allowed.

# Buffer to save the PowerPoint file, previously defined in the server.py file
PPTX_BUFFER = pptx_buffer # Do not modify this line, it is defined in the server.py file

# Width in inches for the image to be added
width = 2  # Example width, modify as needed

# If images are needed, they would be preloaded by the server and passed here.
LIST_OF_BYTES_IO_IMAGES = images #  # Do not modify this line if images are needed, it is defined in the server.py file 

# Initialize a new Presentation instance
prs = Presentation() 

# slides ratio has to be 16:9 not 4:3
prs.slide_width = Inches(13.333333)
prs.slide_height = Inches(7.5)

# Generate here the necessary transformations for generating the PowerPoint presentation according to the user's request. Use titles, subtitles, diagrams, tables, colors, clear fonts, and other elements to make the presentation visually appealing and easy to understand.

# Ensure the pointer is at the start
LIST_OF_BYTES_IO_IMAGES[0].seek(0)
# Example of adding the first image from the list to the presentation, modify the left and top parameters as needed to position the image correctly on the slide
prs.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[0], left=Inches(5.2), top=Inches(1.2), width=Inches(width))

# Save the presentation
prs.save(PPTX_BUFFER) # Do not modify this line, it is defined in the server.py file
```

Provide a complete Python script following this template to generate your PowerPoint presentation.

> **Reminder:** keep the buffer assignment line `PPTX_BUFFER = pptx_buffer` exactly as shown. If this line is omitted or renamed, the script will fail.

When generation is successful, the chat UI shows a download button for the generated file.

### Optional — generate or edit images with seaborn / pillow

`scipy`, `seaborn`, `matplotlib`, and `pillow` are also available. You can render a chart or edit an image **in memory** and append it to `LIST_OF_BYTES_IO_IMAGES` (the same list that holds uploaded images), then place it with `prs.shapes.add_picture(...)`:

```python
import io, matplotlib
matplotlib.use("Agg")              # headless backend
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.lineplot(x=[1, 2, 3, 4], y=[10, 14, 9, 18], marker="o", ax=ax)
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150, bbox_inches="tight"); plt.close(fig); buf.seek(0)
LIST_OF_BYTES_IO_IMAGES.append(buf)            # add the generated image to the list
LIST_OF_BYTES_IO_IMAGES[-1].seek(0)
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.shapes.add_picture(LIST_OF_BYTES_IO_IMAGES[-1], left=Inches(2), top=Inches(1.5), width=Inches(9))
```

To edit an uploaded image instead: open `LIST_OF_BYTES_IO_IMAGES[i]` with `PIL.Image`, edit, save to a new `BytesIO`, `seek(0)`, `append`, then `add_picture`. Always `seek(0)` right before adding (it consumes the stream).

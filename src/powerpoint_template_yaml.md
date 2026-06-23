Use this tool to create a PowerPoint presentation from a structured YAML definition.

A presentation has exactly two top-level keys: `theme` (one named style for the whole deck)
and `slides` (an ordered list). There is no per-slide background, header bar, or text-style
field to decide — every slide looks professional from the theme alone. Use `style_override`
only on the rare slide that needs to deviate from the theme.

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

## Charts: 4 visualization intents (not chart types)

Every chart picks ONE `intent` — never a chart library name. The tool renders it with the
active theme's palette automatically; there is no `palette`, `type`, or `kind` field to set.

| intent | use it for | required fields |
|---|---|---|
| `comparison` | comparing values across categories | `categories` (list of strings) + `values` (list of numbers), same length |
| `trend` | a value changing over time/sequence | `x` (list of numbers) + `y` (list of numbers), same length |
| `distribution` | how a single set of values is spread out | `values` (list of numbers) |
| `part_of_whole` | shares of a total | `categories` (list of strings) + `values` (list of numbers), same length |

`title` is optional on any chart. That's it — no other chart fields exist.

## Optional: style_override (advanced — most slides don't need this)

Only add `style_override` to a slide that must deviate from the active theme. Everything
else about that slide stays normal; every other slide in the deck is unaffected.

```yaml
- type: content_text
  title: "Brand-specific Slide"
  text: "..."
  style_override:
    background: "#0B5FFF"   # explicit hex, or "accent_color" / "background_color"
    header_bar: false       # true | false
```

Available on: `content_text`, `content_image`, `content_mixed`, `content_latex`,
`two_column`, `timeline`. Not available on `cover`/`section_divider` (they always use the
theme's gradient background by design). On `stat_highlight`, only `background` can be
overridden (replaces the gradient with a flat color); `header_bar` does not apply.

Use this tool to create a PowerPoint presentation from a structured YAML definition.

## Canonical example

```yaml
global:
  accent_color: "#60b1fd"    # also: #6D28D9 #E05C3A #059669 #1E293B #334155 #0F4C81
  background_color: "#F0FDFA" # also: #FAF5FF #FFF7F5 #F0FDF4 #F1F5F9 #F8FAFC #F7F9FC
  font_heading: Calibri
  font_body: Calibri
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
    text_style: bullets       # prose | bullets
    header_bar: true          # true(d) | false
    background: background_color  # background_color(d) | accent_color | #RRGGBB
    # not use the same value for background_color and accent_color in one slide.
  - type: two_column
    title: "⚖️ Compare"
    left:  {title: "A", text: "- x\n- y", text_style: bullets}
    right: {title: "B", text: "- x\n- y"}
  - type: content_mixed        # exactly one of: chart | table | image_id
    title: "📊 Chart"
    text: "optional left text"
    chart:
      type: chart              # required
      kind: bar
      data: {city: ["A","B"], sales: [10,20]}
      x: city
      y: sales
      palette: Blues
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
    layout: full   # full | split (split needs text:)
    text: "Optional prose (no LaTeX here)"
  - type: timeline
    title: "📅 Milestones"
    active_index: 1           # 0-based, highlights one item
    items:
      - {fecha: "Jan 2024", titulo: "Kickoff", emoji: "🚀"}
      - {fecha: "Mar 2024", titulo: "Design",  emoji: "🎨"}
```

> `content_mixed` puts `text` on the left, chart/table/image on the right. Omit `text` to leave left side empty.
> `timeline` requires ≥2 items. `fecha`, `titulo` are strings; `emoji` is optional.

## Chart kinds, required fields & extra params

Universal optional: `title` `xlabel` `ylabel` `palette` `hue` (categorical col; not in `heatmap`/`clustermap`/`pie`; exclude from `columns` in `pair`/`pair_kde`).
**Palettes:** `viridis` `magma` `Blues` `Greens` `Set1` `Set2` `coolwarm` `RdBu` `tab10`

| kind | required beyond `data` | extra params |
|---|---|---|
| `hist` | `x` | `bins`(int/"auto") `kde`(bool) `stat`("count"(d)/"density"/"probability") `multiple`("layer"(d)/"dodge"/"stack"/"fill") |
| `kde` | `x` | `kernel`("gau"(d)/"cos"/"epa"/"biw") `bw_adjust`(float,d=1) `fill`(bool) `y`(col→2D) `multiple`("layer"(d)/"stack"/"fill") — multi-kernel: `kernels:["gau","epa"]` + `bw_adjusts:[0.5,1.0]` |
| `ecdf` | `x` | `stat`("proportion"(d)/"count"/"percent") |
| `ridge` | `x` `group` | `overlap`(float,d=0.5) |
| `count` | `x` | `orient`("v"(d)/"h") `order`(list) |
| `scatter` | `x` `y` | `style`(col) `alpha`(float) `fit_reg`(bool) |
| `line` `timeseries` | `x` `y` | `y` can be list→multiple series; `markers`(bool) `ci`(0–99,d=95) `dashes`(bool) |
| `lmplot` | `x` `y` | `order`(int,d=1) `ci`(int) `scatter`(bool) `line_kws`(dict) |
| `lmplot_facet` `timeseries_facet` | `x` `y` `col` | `col_wrap`(int,d=3) |
| `resid` | `x` `y` | `lowess`(bool) |
| `joint` `joint_hex` `joint_kde` | `x` `y` | `kind`("scatter"(d)/"kde"/"hist"/"hex"/"reg") |
| `logistic` | `x` `y` | — |
| `bubble` | `x` `y` `size` | `sizes`([min,max]) `alpha`(float) |
| `bar` `point` | `x` `y` | `ci`(int) `orient`("v"(d)/"h") `markers`(str/list) `linestyles`(str/list) |
| `box` `boxen` | `x` `y` | `orient`("v"(d)/"h") `notch`(bool) |
| `violin` | `x` `y` | `inner`("box"(d)/"quart"/"point"/"stick"/null) `split`(bool,hue=2 groups) |
| `strip` | `x` `y` | `jitter`(bool) `alpha`(float) |
| `swarm` | `x` `y` | `size`(float,d=4) |
| `pie` | `x` `y` | — |
| `heatmap` `clustermap` | `columns` | `method`("pearson"(d)/"spearman"/"kendall") `mask_upper`(bool) `annot`(bool,d=true) `fmt`(str,d=".2f") `vmin`/`vmax`(float) |
| `pair` `pair_kde` | `columns` | `diag_kind`("kde"(d)/"hist") `kind`("scatter"(d)/"kde"/"reg") `corner`(bool) |

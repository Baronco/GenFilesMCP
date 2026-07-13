## Usage Examples

## Table of Contents

- [Example 1: Generating a DOCX file](#example-1-generating-a-docx-file)
  - [Results Summary](#results-summary-📊)
  - [Models that support images](#models-that-support-images)
  - [Models that do not support images](#models-that-do-not-support-images)
- [Example 2: Generating a XLSX file](#example-2-generating-a-xlsx-file)
- [Example 3: Generating a PPTX file](#example-3-generating-a-pptx-file)
- [Example 4: Reviewing a DOCX file with comments](#example-4-reviewing-a-docx-file-with-comments)
- [Example 5: Generating a PDF file](#example-5-generating-a-pdf-file)

### Example 1: Generating a DOCX file

> **Word generation modes:** `ENABLE_STRUCTURED_YAML_MODE=false` is the default mode. In this mode the LLM writes Python code and the backend executes it to generate the DOCX. This default mode supports images uploaded in the chat. `ENABLE_STRUCTURED_YAML_MODE=true` is an experimental structured mode where the model decides the logical order of document elements and their content while the backend builds the DOCX from a template instead of executing generated code. This experimental mode aims to replace code generation over time, but not all models perform well yet. The `Results Summary 📊` benchmark below gives a practical idea of which tested models performed best in this mode.

This alpha version includes both DOCX generation approaches. The examples below show the kind of output GenFilesMCP can produce in practice.

<p align="center">
  <img src="../img/NewDocxGen.png" alt="Generating DOCX Example" />
</p>

This new version can include images embedded directly into the generated Word document, sourced from chat uploads. This allows for richer, visual content in the documents without relying on external links.

<p align="center">
  <img src="../img/new_docx_example.png" alt="Generating DOCX Example" />
</p>

Your assistant can generate documents with one column or two columns for academic papers.

When using the structured YAML mode for Word, set `style_doc: report` for a standard one-column layout or `style_doc: ieee` for a two-column, indented academic-paper layout:

```yaml
style_doc: ieee
cover:
  title: "Gradient Descent"
  subtitle: "A concise review"
  author: "AI Assistant"
  month: "Jul"
  year: "2026"
  page_break: true
body:
  - {type: header, text: "1. Introduction", level: 1}
  - {type: paragraph, text: "Gradient descent is an iterative optimization algorithm..."}
  - {type: equation, latex: '\\theta := \\theta - \\alpha \\nabla J(\\theta)', caption: "Update rule"}
```

You can find results like this in the `example\DOCX` folder of the repository. Each document was exported manually as .pdf to be able to view the results in github, but you can find the original .docx files in the same folder.

#### Results Summary 📊

Scoring scale: `1 = full star`, `0.5 = half star`, `0 = empty star`.

Criteria (brief):
- **C1 Image Use**: correct and meaningful integration of provided images.
- **C2 Structure**: logical flow and coherence.
- **C3 Word Elements**: good use of title/sections/tables/lists/images/formatting.
- **C4 Depth**: ability to develop the topic with complete, well-elaborated paragraphs (not short, shallow ones).
- **C5 First-Try Success**: generated successfully on first attempt.

##### Models that support images

<table align="center">
  <thead>
    <tr>
      <th>Model</th>
      <th>C1</th>
      <th>C2</th>
      <th>C3</th>
      <th>C4</th>
      <th>C5</th>
      <th>Total</th>
      <th>Stars</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>GPT 4.1 mini</td><td>0</td><td>1</td><td>0.5</td><td>0.5</td><td>1</td><td>3.0</td><td>★★★☆☆</td></tr>
    <tr><td>GPT 5.1 mini</td><td>0.5</td><td>0.5</td><td>1</td><td>0.5</td><td>1</td><td>3.5</td><td>★★★⯪☆</td></tr>
    <tr><td>GPT 5.1 Codex mini</td><td>0.5</td><td>1</td><td>0.5</td><td>1</td><td>1</td><td>4.0</td><td>★★★★☆</td></tr>
    <tr><td>GPT 5.2</td><td>1</td><td>1</td><td>0.5</td><td>1</td><td>1</td><td>4.5</td><td>★★★★⯪</td></tr>
    <tr><td>Claude 3 Haiku</td><td>0</td><td>1</td><td>0.5</td><td>0.5</td><td>1</td><td>3.0</td><td>★★★☆☆</td></tr>
    <tr><td>Claude Haiku 4.5</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>5.0</td><td>★★★★★</td></tr>
    <tr><td>Google Gemini 3 Flash Preview</td><td>0.5</td><td>1</td><td>1</td><td>1</td><td>0</td><td>3.5</td><td>★★★⯪☆</td></tr>
    <tr><td>Gemini 3 Pro Preview</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0.0</td><td>☆☆☆☆☆</td></tr>
    <tr><td>Grok Code 4.1 Fast</td><td>1</td><td>1</td><td>0.5</td><td>0.5</td><td>1</td><td>4.0</td><td>★★★★☆</td></tr>
    <tr><td>Kimi K2.5</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>5.0</td><td>★★★★★</td></tr>
    <tr><td>Mistral 14B 2512</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0.0</td><td>☆☆☆☆☆</td></tr>
    <tr><td>Qwen3 VL 8B Thinking</td><td>0.5</td><td>0.5</td><td>1</td><td>0</td><td>1</td><td>3.0</td><td>★★★☆☆</td></tr>
  </tbody>
</table>

##### Models that do not support images

<table align="center">
  <thead>
    <tr>
      <th>Model</th>
      <th>C1</th>
      <th>C2</th>
      <th>C3</th>
      <th>C4</th>
      <th>C5</th>
      <th>Total</th>
      <th>Stars</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Grok Code Fast 1</td><td>N/A</td><td>1</td><td>1</td><td>1</td><td>1</td><td>4.0</td><td>★★★★☆</td></tr>
    <tr><td>DeepSeek V3.1 Terminus</td><td>N/A</td><td>1</td><td>1</td><td>1</td><td>1</td><td>4.0</td><td>★★★★☆</td></tr>
  </tbody>
</table>


- 🏆 **Best overall**: Claude Haiku 4.5 and Kimi K2.5 (5.0/5).
- ✅ **Acceptable performance (4.0 to <5.0)**: GPT 5.2 (4.5), GPT 5.1 Codex mini (4.0), Grok Code 4.1 Fast (4.0), Grok Code Fast 1 (4.0), DeepSeek V3.1 Terminus (4.0).
- ⚠️ **Weakest results**: Gemini 3 Pro Preview (0.0) and Mistral 14B 2512 (0.0).
- ℹ️ In this evaluation, **C1 = 0** means the model failed to call the tool needed to identify attached images.
- 🔎 Content factuality, hallucinations, and technical correctness were **not** evaluated here, because this benchmark focuses on structure, tool use, and first-pass execution; users must validate factual quality independently.


> If your model does not have vision capabilities do not attach images in the chat, as the agent will not be able to see them and include them in the document.

### Example 2: Generating a XLSX file


<p align="center">
  <img src="../img/excel1.png" alt="Generating XLSX Example 1" />
</p>

Open the generated file in Excel:

<p align="center">
  <img src="../img/excel2.png" alt="Generating XLSX Example 2" />
</p>

> **Example files**: You can find example XLSX files in the `example` folder.

### Example 3: Generating a PPTX file

In this example, another MCP server was used for web research and GenFiles MCP Server was used to generate a PowerPoint presentation:

<p align="center">
  <img src="../img/powerpoint1.png" alt="Generating PPTX Example 1" />
</p>

Open the generated file in PowerPoint:

<p align="center">
  <img src="../img/powerpoint2.png" alt="Generating PPTX Example 2" />
</p>

> **Example files**: You can find example PPTX files in the `example` folder.

The structured YAML mode for PowerPoint supports themes, executive-chart intents, and slide types such as `stat_highlight` for KPI cards. Use `intent` to describe the chart purpose and let the backend pick a suitable chart type, or set `chart_type` explicitly:

```yaml
theme: corporate_blue
slides:
  - {type: cover, title: "🚀 Q2 Results", subtitle: "Executive summary", date: "Jul 2026"}
  - {type: stat_highlight, value: "40%", label: "YoY growth", supporting_text: "Driven by new enterprise accounts"}
  - type: content_mixed
    title: "📊 Revenue by Region"
    chart:
      intent: comparison
      categories: ["North", "South", "East", "West"]
      values: [120, 95, 140, 110]
      value_format: currency
```

### Example 4: Reviewing a DOCX file with comments

The review feature allows the agent to analyze uploaded documents and add structured comments for improvements.

<p align="center">
  <img src="../img/reviewer1.png" alt="Review Example 1" />
</p>

<p align="center">
  <img src="../img/reviewer2.png" alt="Review Example 2" />
</p>

**Workflow:**
1. User uploads `History_of_Neural_Nets_Summary.docx` to the chat
2. User requests a review with comments for corrections, grammar suggestions, and idea enhancements
3. Agent calls the `chat_context` custom tool to retrieve file ID and name
4. Agent uses the `list_docx_elements` tool to analyze the document structure
5. Agent calls the `review_docx` tool to add comments to specific elements

**Result:**

<p align="center">
  <img src="../img/docxcomments.png" alt="DOCX Comments" />
</p>

> **Example files**: Find the reviewed document in the `example` folder: `History_of_Neural_Nets_Summary_69d1751b-577b-4329-beca-ac16db7acdbd_reviewed.docx`

> Generated using the GenFiles MCP Server and GPT-5 mini

> The review functionality preserves the original formatting while adding structured comments

### Example 5: Generating a PDF file

The server can generate PDF files using code-based generation. The quality of the generated PDF depends on the model used, with the latest GPT models or Claude models could produce good results.

> This alpha version does not support images in PDF generation, but the backend can generate multi-page PDFs with formatted text, titles, sections, and lists.

This example use the Microsoft learn MCP for search documentation and GenFiles MCP Server for PDF generation:


<p align="center">
  <img src="../img/pdf0.png" alt="Generating PDF Example 1" />
</p>

Open the generated PDF file using Claude Sonnet 4.6:

<p align="center">
  <img src="../img/pdf2.png" alt="Generating PDF Example 2" />
</p>

> **Example files**: You can find example PDF files in the `example` folder, the prefix of this examples ar `Azure_Functions_Python_SDK_Guide`.
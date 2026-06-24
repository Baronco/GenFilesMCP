# File Generation Skills

On-demand authoring guides for the GenFiles file-generation tools. Each skill is plain markdown,
meant to be carried into a client that loads skills on demand (progressive disclosure) — the
GenFiles server itself does not serve these files. Moving the detailed instructions here keeps the
tools' OpenAPI descriptions short and generic so they no longer flood the model's context.

## One skill per file type

| Skill | Modes | Backing tools |
|---|---|---|
| [word](word/) | python generation · YAML generation · review | `generate_word` / `generate_word_structured_yaml`, `list_docx_elements`, `review_docx` |
| [powerpoint](powerpoint/) | python generation · YAML generation | `generate_powerpoint` / `generate_powerpoint_structured_yaml` |
| [excel](excel/) | python generation | `generate_excel` |
| [pdf](pdf/) | python generation | `generate_pdf` |
| [markdown](markdown/) | python generation | `generate_markdown` |

## Layout

One `SKILL.md` per skill — a single self-contained markdown file per file type:

```text
skills/<type>/
└── SKILL.md                 # frontmatter + all authoring modes for that file type
```

## SKILL.md format (Anthropic Agent Skills convention)

Begin with YAML frontmatter, then the body covering every authoring mode the file type supports:

```markdown
---
name: <type>-generation
description: <one concise sentence: what it does + which modes; used for discovery>
---

Body that: lists the modes ("use this when…"), names `fetch_uploaded_chat_file_ids` as the tool
for pulling uploaded chat files/images, and then documents each mode in full (script template /
YAML schema / review workflow) under its own section.
```

Keep `name` kebab-case and unique, and keep `description` to one sentence (it is the discovery
surface). Word covers three modes (python / yaml / review), PowerPoint two (python / yaml), and
Excel / PDF / Markdown one (python) — all inside the single `SKILL.md`.

## Getting uploaded files/images from the chat

Every skill points to the **`fetch_uploaded_chat_file_ids`** tool. Call it to obtain the IDs of
files/images uploaded in the current chat **before** generating files that embed uploaded images
(Word / PowerPoint / PDF) or **before** reviewing a Word document (to get the document's file ID).

## Generating images in code mode

The python-generation references for Word, PowerPoint, and PDF document how to render a chart with
`seaborn`/`matplotlib` (or edit an image with `pillow`) in memory and append it to the `images`
byte-list the template exposes, so the builder can place it alongside any pre-uploaded images.
`scipy`, `seaborn`, and `pillow` are available. Excel has no preloaded image list (charts are built
and embedded in-script via `openpyxl`); Markdown is text-only and cannot embed binary images.

# doc2md

Hermes Agent skill for converting documents to Markdown ready for LLMs.

Supports PDF, Office documents, ODT/ODS/ODP, RTF, EPUB, CSV, HTML, JSON, XML, ZIP, TXT, and IPYNB, with automatic routing between PaddleOCR, anydoc, and MarkItDown.

## Usage

```bash
~/.hermes/skills/doc2md/scripts/convert2md document.docx -o document.md
~/.hermes/skills/doc2md/scripts/convert2md scan.pdf
```

The `.venv/` directory contains the skill's local dependencies and is not versioned. See `SKILL.md` for installation, options, and limitations.

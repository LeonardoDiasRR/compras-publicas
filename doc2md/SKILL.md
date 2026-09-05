---
name: doc2md
description: "Use when converting documents to Markdown for LLMs."
license: MIT
---

# doc2md — Universal document-to-Markdown conversion

Converts any document to clean Markdown ready for LLM consumption
(feeding, RAG, source ingestion into LLM Wiki, summaries). One command,
automatic routing by extension. Nothing is installed system-wide: all three
engines live in the skill's own venv.

## Engines and routing

| Format                                   | Engine                    | Fallback   |
|------------------------------------------|---------------------------|------------|
| `.pdf` (any, including scanned)          | PaddleOCR PP-StructureV3  | — (spec)   |
| `.doc` `.docx` `.docm` `.ppt*` `.xls*` `.odt` `.ods` `.odp` `.rtf` `.epub` `.csv` | anydoc (Firecrawl) | markitdown |
| `.html` `.json` `.xml` `.zip` `.txt` `.ipynb` | markitdown           | —          |

- **PDF → PaddleOCR**: PP-StructureV3 pipeline (layout, tables, formulas,
  OCR for scanned pages). The first run downloads models (hundreds of MB)
  to `~/.paddlex`; they are then cached.
- **other formats → anydoc**: local Rust (Firecrawl), <5 ms/doc, consistent
  GFM Markdown. On failure (e.g. `NeedsOcr`, `Encrypted`) → markitdown fallback.
- **markitdown**: universal fallback (Microsoft).

Force an engine at any time with `--engine paddle|anydoc|markitdown` —
useful for PDFs with a text layer: `--engine anydoc` extracts in milliseconds
instead of using OCR (Paddle is slow on large pages).

## CLI usage

```bash
SKILL=~/.hermes/skills/doc2md
$SKILL/scripts/convert2md report.pdf -o report.md           # single file (PDF -> PaddleOCR)
$SKILL/scripts/convert2md folder/*.docx -d output/          # batch -> output/*.md
$SKILL/scripts/convert2md scan.pdf --engine anydoc          # text-layer PDF, fast
$SKILL/scripts/convert2md doc.docx                          # markdown to stdout
$SKILL/scripts/convert2md doc.docx --lang en                # Paddle OCR language (Latin default, covers pt)
```

- Output: stdout when `-o`/`-d` is not provided; otherwise `.md` file(s).
- Exit code: `0` success, `1` conversion error, `2` invalid usage.
- With `-v`, prints the engine used for each file to stderr.

## Python usage (for agents that want the string in memory)

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home()/".hermes/skills/doc2md/scripts"))
import convert2md as c
md = c.convert_anydoc(Path("doc.docx"))      # direct engine
PY
```

In practice, prefer the CLI: the `scripts/convert2md` wrapper automatically
uses the correct venv (`exec scripts/convert2md <args>`).

## Local installation (inside the skill directory)

Everything is installed in `~/.hermes/skills/doc2md/.venv` (Python 3.13, via uv):

| Project          | Package            | Installed version (2026-08-28) |
|------------------|-------------------|-------------------------------|
| PaddleOCR        | `paddleocr` + `paddlepaddle` | 3.7.0 / **3.2.2** (3.3.1 has an oneDNN/PIR bug, see references/install.md) |
| Firecrawl anydoc | `firecrawl-anydoc` | 0.2.4 (wheel abi3 manylinux) |
| Microsoft MarkItDown | `markitdown[pdf,docx,pptx,xlsx]` | 0.1.7 |

### Downloading PaddleOCR models

During installation, ask the user whether they want to download approximately
700 MB of PaddleOCR models to `~/.paddlex`. Run the detailed warm-up procedure
in `references/install.md` only after consent. If the user declines, do not
download the models.

For the complete reproduction procedure, commands, and version pins, see
`references/install.md`. Format detection fixtures are in the anydoc repo at
`tests/fixtures/`.

## Verification (self-test)

```bash
~/.hermes/skills/doc2md/scripts/self_test.sh
```

Downloads example fixtures from the anydoc repo (docx/xlsx/pptx/text PDF/scanned
PDF) to /tmp and converts them with all three engines, validating that the
output is not empty. Requires network access to download the fixtures and, if
the models are absent, the first Paddle use may attempt to download them.

## Pitfalls

- **paddlepaddle must be 3.2.2** on this host: 3.3.1 breaks the layout model
  (oneDNN/PIR); the downgrade is documented in `references/install.md`.
- **The default PDF path may try to download missing PaddleOCR models** during
  a later conversion. During installation, ask the user before the
  warm-up/download; if they decline, the models are not downloaded at that
  time. Scanned PDFs require PaddleOCR; PDFs with a text layer can use
  `--engine anydoc` or `--engine markitdown` without the models.
- **Paddle is CPU-only and slow on large PDFs** (page-by-page OCR). Plain text
  → prefer `--engine anydoc`. Scanned/image documents → Paddle is the right path.
- **anydoc does not perform OCR**: a scanned PDF through anydoc raises
  `NeedsOcr`. Since the default PDF engine is Paddle, this only appears when
  `--engine anydoc` is forced.
- PaddleOCR's `doc2md_convert` (docx/pptx/xlsx → md) exists, but it is
  VLM-based and slower; use anydoc for Office documents (the default) — it is
  much faster.
- Output preserves images only as alt text/links (all engines); image bytes
  remain in the document model, not in the Markdown.
- The venv is large (~1.5 GB+ with Paddle). Do not duplicate it per project —
  use the skill via its absolute path.

## Related

- `llm-wiki` (repo ~/llm-wiki): use this skill to convert sources to Markdown
  in `raw/` before ingestion. Do not duplicate document skills — this is the
  only one.

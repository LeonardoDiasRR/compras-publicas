# PaddleOCR Download Consent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document an explicit user opt-in during skill installation before downloading PaddleOCR's local models.

**Architecture:** This is a documentation-only change. `references/install.md` will contain the executable consent flow and warm-up command; `SKILL.md` will summarize the policy and link to the detailed procedure. `scripts/convert2md.py` remains non-interactive and unchanged.

**Tech Stack:** Markdown, Bash, Python 3.13, PaddleOCR PP-StructureV3.

## Global Constraints

- O download dos modelos locais do PaddleOCR deve ser explicitamente opt-in durante a instalação da skill, sem introduzir uma consulta interativa na primeira conversão.
- Os modelos ocupam aproximadamente 700 MB, exigem rede e são armazenados em `~/.paddlex`.
- PDFs escaneados dependem do PaddleOCR; PDFs com camada de texto podem usar `anydoc` ou `markitdown`.
- Não alterar o script `convert2md`, que continuará sem interação.
- Não criar dependências, scripts auxiliares ou commits; a alteração fica limitada à documentação solicitada.

---

## Phase 1: Documentação Do Consentimento

> **Execution:** Executed by 2 independent subagents in parallel — one subagent per task, no ordering between tasks.

### Task 1: Procedimento De Instalação

**Files:**
- Modify: `references/install.md` after the dependency installation commands and before `Observações`

**Interfaces:**
- Consumes: the existing `SKILL` variable and the installed virtual environment described by the reproduction commands.
- Produces: a copy-pasteable opt-in prompt and a one-time `PPStructureV3` initialization command for the installation operator.

- [ ] **Step 1: Add the consent section**

Insert a section titled `## Download dos modelos do PaddleOCR` after the three dependency-installation commands. State that package installation does not itself download the model files, that the first PDF conversion would otherwise trigger a download of approximately 700 MB into `~/.paddlex`, and that the operator must ask the user before proceeding.

- [ ] **Step 2: Add the exact prompt and accepted response**

Add this Bash flow, using a negative default so pressing Enter refuses the download:

```bash
read -r -p "Baixar agora os modelos do PaddleOCR (~700 MB) para ~/.paddlex? [y/N] " answer
case "$answer" in
  [Yy]|[Yy][Ee][Ss])
    "$SKILL/.venv/bin/python" -c 'from paddleocr import PPStructureV3; PPStructureV3(use_doc_orientation_classify=True, use_doc_unwarping=True, use_textline_orientation=True)'
    ;;
  *)
    echo "Modelos do PaddleOCR não baixados."
    ;;
esac
```

Explain that the `y`/`yes` branch initializes the same PP-StructureV3 pipeline used by `convert2md.py`, causing the model files to be downloaded and cached locally; any other response skips the download.

- [ ] **Step 3: Document the two resulting operating modes**

State that accepting requires network access only for the download and enables the default PDF path, while refusing does not download during installation but leaves the current behavior in place: a later default PDF conversion may try to download missing models. Explicitly state that scanned PDFs require PaddleOCR, whereas text-layer PDFs can be converted with `--engine anydoc` or `--engine markitdown`.

- [ ] **Step 4: Verify the section is internally consistent**

Run:

```bash
rg -n "Download dos modelos|Baixar agora|~700 MB|~\\.paddlex|anydoc|markitdown" references/install.md
```

Expected: the new section contains the consent prompt, cache path, approximate size, both response branches, and the alternative engines without changing the existing version or dependency commands.

### Task 2: Guia Principal Da Skill

**Files:**
- Modify: `SKILL.md` in the local installation section and the PDF-related pitfalls

**Interfaces:**
- Consumes: the detailed procedure documented in `references/install.md`.
- Produces: a visible installation rule telling the agent to obtain consent before any PaddleOCR model download.

- [ ] **Step 1: Add the opt-in rule to the installation section**

After the installation table and before `Reprodução completa`, add a short subsection titled `### Download dos modelos PaddleOCR`. Tell the agent to ask the user during installation whether to download approximately 700 MB of models to `~/.paddlex`, to execute the detailed warm-up procedure in `references/install.md` only after consent, and not to download anything when the user declines.

- [ ] **Step 2: Clarify the effect of declining**

Update the existing PDF pitfalls so they distinguish installation from first use: the default PDF route may download missing models during a later conversion if installation was declined, and a PDF with a text layer can use `--engine anydoc` or `--engine markitdown` without them. Preserve the existing warning that scanned PDFs need PaddleOCR.

- [ ] **Step 3: Verify the guide points to the detailed instructions**

Run:

```bash
rg -n "consent|pergunte|700 MB|~\\.paddlex|references/install.md|não.*baix|anydoc|markitdown" SKILL.md
```

Expected: the main guide contains the opt-in instruction, the cache location, the refusal behavior, the detailed-document reference, and the text-layer alternatives.

## Phase 2: Integration Verification

> **Execution:** Executed by 1 independent subagent after Phase 1 completes. This phase must run after Phase 1 because it checks the combined documentation.

### Task 3: Revisão Final Da Documentação

**Files:**
- Read-only verification of `SKILL.md`, `references/install.md`, and `scripts/convert2md.py`

**Interfaces:**
- Consumes: both documentation edits from Phase 1 and the unchanged conversion script.
- Produces: verification evidence that the documented command matches the script's PaddleOCR options and that no implementation file was modified.

- [ ] **Step 1: Check for placeholders and accidental implementation changes**

Run:

```bash
rg -n "TBD|TODO|PLACEHOLDER" docs/superpowers/plans/2026-08-29-paddleocr-download-consent.md SKILL.md references/install.md
git diff -- scripts/convert2md.py
```

Expected: no placeholder matches and no diff for `scripts/convert2md.py`.

- [ ] **Step 2: Check the documented pipeline options**

Compare the warm-up command in `references/install.md` with `convert_paddle` in `scripts/convert2md.py`. Confirm that both initialize `PPStructureV3` with `use_doc_orientation_classify=True`, `use_doc_unwarping=True`, and `use_textline_orientation=True`.

- [ ] **Step 3: Review the complete diff**

Run:

```bash
git diff --check
git diff --stat
git status --short
```

Expected: whitespace validation succeeds; only the two requested documentation files are modified by implementation, alongside the already-created design and plan documents.

#!/usr/bin/env bash
# Self-test do doc2md: converte um lote de formatos e valida saídas não vazias.
# Requer rede para baixar fixtures do repo anydoc; no 1º run do Paddle, modelos.
set -u
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTDIR="${1:-/tmp/doc2md_selftest}"
FIX="https://raw.githubusercontent.com/firecrawl/anydoc/main/tests/fixtures"
CONV="$SKILL/scripts/convert2md"
mkdir -p "$TESTDIR"
cd "$TESTDIR" || exit 1

fail=0
run() { # name engine file
  echo "--- $1 ---"
  if out=$("$CONV" "$3" --engine "$2" -o "$TESTDIR/$1.md" 2>&1); then
    size=$(wc -c < "$TESTDIR/$1.md")
    echo "OK: $1.md ($size bytes)"
    [ "$size" -gt 0 ] || { echo "FALHOU: saída vazia"; fail=1; }
  else
    echo "FALHOU: $out"
    fail=1
  fi
}

# baixa fixtures (ignora se já existem)
fetch() { [ -f "$TESTDIR/$2" ] || curl -sL -o "$TESTDIR/$2" "$FIX/$1"; }
fetch docx/handmade-rich.docx sample.docx
fetch xlsx/sheet.xlsx sample.xlsx
fetch pptx/pres.pptx sample.pptx
fetch pdf/text.pdf sample-text.pdf
fetch pdf/handmade-scanned.pdf sample-scanned.pdf

run docx        anydoc      "$TESTDIR/sample.docx"
run xlsx        anydoc      "$TESTDIR/sample.xlsx"
run pptx        anydoc      "$TESTDIR/sample.pptx"
run pdf-text    paddle      "$TESTDIR/sample-text.pdf"
run pdf-scan    paddle      "$TESTDIR/sample-scanned.pdf"
run docx-fb     markitdown  "$TESTDIR/sample.docx"

echo
[ "$fail" -eq 0 ] && echo "SELF-TEST OK" || echo "SELF-TEST COM FALHAS"
exit $fail
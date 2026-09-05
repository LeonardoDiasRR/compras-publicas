#!/usr/bin/env python3
"""Conversão universal de documentos para Markdown (para consumo por LLM).

Roteamento por extensão:
  .pdf            -> PaddleOCR (PP-StructureV3)  [obrigatório para PDF]
  demais formatos -> anydoc (Firecrawl), fallback -> markitdown (Microsoft)

Formatos suportados (anydoc): doc, docx, docm, ppt, pps, pot, pptx, pptm,
ppsx, ppsm, xls, xlsx, xlsm, xlsb, odt, ods, odp, rtf, epub, csv.
markitdown (fallback) cobre também: html, json, xml, zip, imagens, audio.

Uso:
  convert2md ARQUIVO...                 # markdown no stdout
  convert2md ARQUIVO -o saida.md        # arquivo único -> saida.md
  convert2md ARQUIVO... -d pasta/       # múltiplos -> pasta/<nome>.md
  convert2md ARQUIVO --engine e         # forçar motor: paddle|anydoc|markitdown

Exit code: 0 ok, 1 erro de conversão (com mensagem), 2 uso inválido.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ENGINES = ("auto", "paddle", "anydoc", "markitdown")
ANYDOC_EXTS = {
    ".doc", ".docx", ".docm",
    ".ppt", ".pps", ".pot", ".pptx", ".pptm", ".ppsx", ".ppsm",
    ".xls", ".xlsx", ".xlsm", ".xlsb",
    ".odt", ".ods", ".odp",
    ".rtf", ".epub", ".csv",
}
PDF_EXTS = {".pdf"}
FALLBACK_EXTS = {".html", ".htm", ".json", ".xml", ".zip", ".txt", ".md", ".ipynb"}


def engine_for(path: Path, engine: str) -> list[str]:
    """Retorna a ordem de motores a tentar para o arquivo."""
    ext = path.suffix.lower()
    if engine != "auto":
        return [engine]
    if ext in PDF_EXTS:
        return ["paddle"]
    if ext in ANYDOC_EXTS:
        return ["anydoc", "markitdown"]
    if ext in FALLBACK_EXTS:
        return ["markitdown"]
    return ["anydoc", "markitdown"]


def convert_anydoc(path: Path) -> str:
    import anydoc
    return anydoc.to_markdown(str(path))


def convert_markitdown(path: Path) -> str:
    from markitdown import MarkItDown
    return MarkItDown().convert(str(path)).text_content


_paddle = None


def convert_paddle(path: Path, lang: str) -> str:
    """PaddleOCR PP-StructureV3: PDF -> Markdown (instância em cache)."""
    global _paddle
    if _paddle is None:
        from paddleocr import PPStructureV3
        _paddle = PPStructureV3(
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
            lang=lang or None,
        )
    results = _paddle.predict(input=str(path))
    pages = []
    for r in results:
        m = getattr(r, "markdown", None)
        md = m if isinstance(m, str) else (m or {}).get("markdown_texts", "") or ""
        if not md:
            # ponytail: fallback pelo exportador oficial (escreve <stem>_<page>.md)
            with tempfile.TemporaryDirectory() as tmp:
                r.save_to_markdown(tmp)
                for f in sorted(Path(tmp).glob("*.md")):
                    md += f.read_text(encoding="utf-8") + "\n\n"
        if md.strip():
            pages.append(md.strip())
    if not pages:
        raise RuntimeError("PaddleOCR não retornou markdown para o documento")
    return "\n\n".join(pages)


def convert(path: Path, engine: str, lang: str, verbose: bool) -> str:
    for eng in engine_for(path, engine):
        try:
            if verbose:
                print(f"[convert2md] {path.name}: motor={eng}", file=sys.stderr)
            if eng == "paddle":
                return convert_paddle(path, lang)
            if eng == "anydoc":
                return convert_anydoc(path)
            if eng == "markitdown":
                return convert_markitdown(path)
        except Exception as e:
            last = f"{eng}: {e}"
            if verbose:
                print(f"[convert2md] {path.name}: {eng} falhou ({e})", file=sys.stderr)
    raise RuntimeError(f"nenhum motor converteu {path.name} — último erro: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="arquivos a converter")
    ap.add_argument("-o", "--out", help="arquivo de saída (apenas 1 entrada)")
    ap.add_argument("-d", "--out-dir", help="diretório de saída (preserva nomes)")
    ap.add_argument("--engine", choices=ENGINES, default="auto", help="forçar motor")
    ap.add_argument("--lang", default="", help="idioma OCR do PaddleOCR (vazio = modelo multilingue default, cobre pt; ex.: en, ch)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if args.out and len(args.inputs) > 1:
        ap.error("-o só é válido com um único arquivo de entrada")
    if args.out_dir:
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    rc = 0
    for src in args.inputs:
        path = Path(src)
        if not path.is_file():
            print(f"ERRO: arquivo não encontrado: {src}", file=sys.stderr)
            rc = 1
            continue
        try:
            md = convert(path, args.engine, args.lang, args.verbose)
        except Exception as e:
            print(f"ERRO: {path.name}: {e}", file=sys.stderr)
            rc = 1
            continue

        if args.out:
            Path(args.out).write_text(md, encoding="utf-8")
            print(args.out)
        elif args.out_dir:
            out = Path(args.out_dir) / (path.stem + ".md")
            out.write_text(md, encoding="utf-8")
            print(out)
        else:
            print(md, end="" if md.endswith("\n") else "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
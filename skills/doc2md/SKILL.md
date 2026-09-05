---
name: doc2md
description: "Use antes de ler qualquer documento de contratação baixado (anexos PNCP: TR, edital, ata, PDFs de ARP, docx/xlsx/zip): converta para Markdown com o doc2md convert2md.py e depois leia o .md. Cobre invocação no Windows e escolha de motor."
---

# doc2md — conversão de documentos para Markdown (leitura por LLM)

Conversor vendorado em `doc2md/` (repo LeonardoDiasRR/doc2md). Converter SEMPRE
para Markdown antes de ler anexos de contratações/ARPs (PDF, docx, xlsx, zip,
html...) — nunca tentar "ler" o binário diretamente.

## Como chamar (o wrapper bash `scripts/convert2md` é Linux-only; chame o python do venv)

```bash
# Linux
PY=doc2md/.venv/bin/python
# Windows (PowerShell)
# $PY = "doc2md/.venv/Scripts/python.exe"

& $PY doc2md/scripts/convert2md.py TR.pdf -o TR.md --engine markitdown   # PDF com camada de texto
& $PY doc2md/scripts/convert2md.py edital.docx -d out/                    # lote -> out/*.md
& $PY doc2md/scripts/convert2md.py doc.docx                               # md no stdout
```

Instalação do venv (clone novo): `cd doc2md && uv venv .venv && uv pip install -p .venv "markitdown[pdf,docx,pptx,xlsx]"`

## Roteamento de motores

| Formato | Motor | Nota |
|---|---|---|
| `.docx .pptx .xlsx .pdf(texto) .html .json .xml .csv .zip .txt` | markitdown | único instalado aqui; rápido, sem modelo |
| PDF escaneado | paddle (PP-StructureV3) | **não instalado** (venv ~1,5 GB + ~700 MB de modelos); exigir só com consentimento — ver `doc2md/references/install.md` |
| Office via anydoc | — | roda só em Linux (wheel manylinux); aqui cai em markitdown |

`--engine paddle|anydoc|markitdown` força motor; sem `--engine`, PDF vai para
paddle e falha com ImportError — para PDF de banco (Comprasnet/PNCP quase
sempre tem camada de texto) use **`--engine markitdown`**.

## Fluxo com anexos PNCP (receita compras-publicas)

1. Baixe o arquivo da API pública (`.../arquivos/{seq}`) para um `.bin`.
2. Se `file`/magic indicar `Zip` (edital costuma ser ZIP dentro de ZIP):
   descompacte os 2 níveis com `zipfile` antes de converter.
3. Converta cada documento com `convert2md.py --engine markitdown -o <nome>.md`.
4. Leia o `.md` e busque a tabela de itens/especificações (Markdown GFM).
5. Tabela que vier quebrada no markitdown: retentar o mesmo PDF com
   `pdftotext -layout` ou (instalado) `--engine paddle`.

## Pitfalls

- PDF sem `--engine markitdown` → tentativa de importar paddle (ausente) → erro.
- markitdown preserva imagens só como alt-text; spec em imagem só via paddle/OCR.
- Não duplicar o venv: usar sempre `doc2md/.venv` pelo caminho absoluto.
- Instalação completa (PaddleOCR p/ escaneados): `doc2md/references/install.md`
  (pin `paddlepaddle==3.2.2`; 3.3.1 quebra o modelo de layout).

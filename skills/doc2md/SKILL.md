---
name: doc2md
description: "Use before reading any downloaded contracting document (anexos PNCP: TR, edital, ata, ARP PDFs, docx/xlsx/zip): convert to Markdown with doc2md convert2md.py, then read the .md. Covers Windows invocation and engine routing."
---

# doc2md — conversão de documentos para Markdown (leitura por LLM)

Conversor vendorado em `doc2md/` (repo LeonardoDiasRR/doc2md). Converter SEMPRE
para Markdown antes de ler anexos de contratações/ARPs (PDF, docx, xlsx, zip,
html...) — nunca tentar "ler" o binário diretamente.

## Como chamar (Windows — esta máquina)

O wrapper bash `scripts/convert2md` é Linux; no Windows chame o python do venv:

```powershell
$D2M = "doc2md/.venv/Scripts/python.exe"
& $D2M doc2md/scripts/convert2md.py TR.pdf -o TR.md          # PDF com camada de texto
& $D2M doc2md/scripts/convert2md.py edital.docx -d out/      # lote -> out/*.md
& $D2M doc2md/scripts/convert2md.py doc.docx                 # md no stdout
```

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

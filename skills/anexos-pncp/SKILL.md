---
name: anexos-pncp
description: "Use quando o usuário pedir para baixar/ler os ARQUIVOS de uma contratação (edital, TR, ETP) ou de Atas de Registro de Preços (ARP) — baixar anexos PNCP, descompactar zip, converter cada arquivo para markdown com doc2md e salvar o .md correspondente."
---

# Anexos de Contratações e ARPs (PNCP) → Markdown

Fluxo obrigatório quando o usuário pedir "os arquivos da contratação" ou "os
arquivos das atas de registro de preços": **baixar → descompactar → converter
cada arquivo para markdown com doc2md → salvar o `.md` ao lado do original**.
Nunca leia PDF/docx/binário cru: leia sempre o `.md` gerado.

## 1. Identificar a contratação/ata

Sempre por `numeroControlePNCP`, nunca por número (homônimos entre órgãos):

- Compra: `numeroControlePncpCompra` = `CNPJ14-1-SEQ/ANO` (ex.:
  `00509018000113-1-002101/2025`). O `sequencial` das rotas/tools é SEM zeros à
  esquerda (`2101`).
- Ata: `numeroControlePncpAta` = `<controle da compra>-NNNNNN` (sufixo = seq da
  ata: `-000004/2024` → ata 4). Vem de `compras_arp_listar` /
  `compras_arp_por_fim_vigencia`.

## 2. Listar os arquivos

Tools MCP (sem chave, sem captcha):

- Contratação: `compras_pncp_contratacao_arquivos {cnpj, ano, sequencial}`
- Ata (+ aditivos): `compras_pncp_ata_arquivos {cnpj, ano_compra, sequencial_compra, sequencial_ata}`

Fora de sessão MCP, API pública direta (base `https://pncp.gov.br/api/pncp`,
rotas em `../compras-publicas/references/pncp-arquivos-api.md`):

```
GET /v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos
GET /v1/orgaos/{cnpj}/compras/{anoCompra}/{seqCompra}/atas/{seqAta}/arquivos
```

Cada item traz `url` (download direto), `titulo`, `tipoDocumentoNome`,
`sequencialDocumento`. Aditivos de ata aparecem como documentos extras do mesmo
tipo — distinguir por `titulo`/`dataPublicacaoPncp`.

## 3. Baixar em pasta temporária

Pasta única por contratação/ata, ex.: `<temp>/pncp_<cnpj>-<ano>-<seq>/`
(ou `..._ata<N>/`). Nome de arquivo: `NNN_<slug-do-titulo>.<ext>` (use
`sequencialDocumento` + trecho do `titulo`, sem espaços). Baixe com GET simples
na `url` (curl/Invoke-WebRequest), sem navegador — a página SPA
`pncp.gov.br/app/editais/...` é protegida por hCaptcha e não carrega em headless.

## 4. Descompactar (inclusive zip aninhado)

O "Edital" costuma vir como ZIP — e **ZIP dentro de ZIP**. Extraia
recursivamente até não sobrar zip, em subpasta com o nome do arquivo de origem:

```python
import zipfile
from pathlib import Path
def extrair_zips(rec: Path):
    novos = True
    while novos:
        novos = False
        for z in rec.rglob("*.zip"):
            d = z.with_suffix("")
            d.mkdir(exist_ok=True)
            with zipfile.ZipFile(z) as f: f.extractall(d)
            novos = True
extrair_zips(Path(pasta))
```

`zipfile` pode falhar em zips com encoding estranho — fallback: `unzip` /
`Expand-Archive` arquivo a arquivo. Confirme com `file`/assinatura mágica que o
"PDF" não é zip disfarçado.

## 5. Converter cada arquivo para Markdown (doc2md)

Para CADA pdf/docx/xlsx/pptx restante, gerar `.md` com o mesmo nome-base, ao
lado do original:

```
Windows: doc2md/.venv/Scripts/python.exe doc2md/scripts/convert2md.py <arquivo> --engine markitdown -o <saida>.md
Linux:   doc2md/.venv/bin/python          doc2md/scripts/convert2md.py <arquivo> --engine markitdown -o <saida>.md
```

- `markitdown` resolve PDFs com camada de texto (bancos emitidos em PDF);
  `paddle`/`anydoc` não estão instalados — escaneado puro exigiria PaddleOCR
  (ver `skills/doc2md/SKILL.md`).
- Itens não conversíveis (imagens, assinaturas .p7s, zip já extraído): pule e
  liste no relatório final.

## 6. Ler e reportar

Leia os `.md` gerados (não os originais). Ao reportar, liste a pasta com
`arquivo original → arquivo .md` e o `titulo`/`tipoDocumentoNome` de cada um.

## Armadilhas (pitfalls)

- `sequencial` sem zeros à esquerda na URL/tools vs controle PNCP com zeros.
- Lote longo: rode em background e salve a saída em arquivo; nunca encaminhe
  saída de rede para interpretador (`| python3`).
- A spec técnica real só existe no TR — o CATMAT/objeto subestima (caso TRE-RN:
  CATMAT "GPU 24 GB", TR exigia 48 GB). Quando o usuário pede os arquivos, o TR
  é quase sempre o que ele quer.
- Pasta temporária ≠ lixo imediato: o usuário pode pedir os `.md` depois;
  informe o caminho no final.

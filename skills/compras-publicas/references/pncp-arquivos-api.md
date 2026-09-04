# PNCP — rota pública de arquivos (baixar TR/edital/ata sem chave)

Verificado em 2026-09-03 com ARP 00103/2025 do TRE-RN (CNPJ 00509018000113, compra 2101/2025).

## Endpoints (base https://pncp.gov.br/api/pncp)

| O que | Rota |
|---|---|
| Documentos da compra | `/v1/orgaos/{cnpj14}/compras/{ano}/{sequencial}/arquivos` |
| Baixar doc N | `/v1/orgaos/{cnpj14}/compras/{ano}/{sequencial}/arquivos/{seqDocumento}` |
| Documentos da ATA | `/v1/orgaos/{cnpj14}/compras/{anoCompra}/{seqCompra}/atas/{seqAta}/arquivos` |
| Documentos do contrato | `/v1/orgaos/{cnpj14}/contratos/{ano}/{sequencial}/arquivos` |
| Termos aditivos do contrato | `/v1/orgaos/{cnpj14}/contratos/{ano}/{seq}/termos/{seqTermo}/arquivos` |
| Tipos de documento | `/v1/tipos-documentos` |
| OpenAPI completo | `/v3/api-docs` (~395 KB, lista tudo) |

Resposta da listagem: `[{url, uri, sequencialDocumento, titulo, tipoDocumentoNome, tipoDocumentoId, dataPublicacaoPncp, statusAtivo}]`. Sem autenticação, sem captcha, funciona via curl direto do servidor.

## O que NÃO funciona (não perder tempo)

- `/api/pncp/v1/contratacoes/{controlePNCP}/{ano}` e variantes → 404/400 (rota interna do SPA, protegida por hCaptcha `x-totally-captcha`; o SPA fica preso em "Carregando..." no headless).
- `/api/consulta/v1/.../documentos` → 404 (esse namespace não tem documentos).
- `compras_contratacoes_14133_listar/consultar` → upstream 404/500 para este caso (não confiáveis).

## Pacote de edital costuma ser ZIP

O download pode ser `Zip archive data` mesmo parecendo PDF. Conteúdo típico (TRE-RN):
```
Edital e anexos/  → Edital, Termo de Referência NN-AAAA.pdf, Minuta ARP, Valor Estimado, Termo de Sigilo
Fase de planejamento/ → ETP, DOD, GR
```
Extraia com `zipfile.extractall` e rode `file` sobre cada PDF (pode haver ZIP aninhado). Converter TR: `~/.hermes/skills/doc2md/scripts/convert2md TR.pdf --engine anydoc -o /tmp/tr.md` (milissegundos; PDF com camada de texto — PaddleOCR só se escaneado).

## Busca de spec no TR

Convertido, busque no markdown: nomes de GPUs (B200/B300/H100/H200/A100/RTX), "GB de memória", CUDA cores, consumo W. A seção numérica (ex. `5.4. GPU TIPO I`) traz a spec mínima real. Caso real: CATMAT da ARP dizia "acelerador GPU 24 GB" e o TR especificava 48 GB GDDR6 ECC / ≥18.000 CUDA / ≤400 W passiva (RTX 6000 Ada-like) — o CATMAT subestima a spec; sempre confirme no TR antes de concluir sobre geração/memória de GPU.

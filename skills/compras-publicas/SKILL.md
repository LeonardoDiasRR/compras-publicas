---
name: compras-publicas
description: "Use ao consultar compras públicas federais: Compras.gov.br, PNCP, ARP, CATMAT, sanções CGU via MCP compras. Receitas, armadilhas, anexos/TR."
---

# Compras Públicas (MCP_Compras + skills da Operação Mitra)

Plugin `compras-publicas`: servidor MCP `MCP_Compras`
(github.com/opedrosoares/MCP_Compras, FastMCP 2.x, ~96 tools somente-leitura —
fork local mantém +2 tools de anexos PNCP, PR #1 upstream) sobre as APIs Dados
Abertos Compras.gov.br, PNCP, Portal da Transparência/CGU e Comprasnet.

## Estrutura do plugin

- Projeto raiz: `~/projetos/compras-publicas/` (repo git; remote GitHub
  LeonardoDiasRR/compras-publicas, privado). Plugin instalado em
  `~/.hermes/plugins/compras-publicas` (symlink para o projeto).
- `MCP_Compras/` — código vendorado (sem .git upstream), venv via `uv sync`.
- `mcp.json` — registra o servidor stdio como plugin portável
  (`compras-publicas__compras` no runtime). Requer o plugin em `plugins.enabled`
  do config.yaml; tools MCP só aparecem em NOVA sessão do Hermes.
- `scripts/mcp_query.py` — cliente stdio JSON-RPC mínimo (uso fora de sessão
  Hermes com as tools): `python3 scripts/mcp_query.py <tool> '<json_args>'`,
  `_list`, `_schema '{"names":[...]}'`.
- `scripts/scan_rack_arps.py`, `scan_gpu_mem.py` — varreduras CATMAT→ARP prontas.
- Opcional: `TRANSPARENCIA_API_KEY` em `MCP_Compras/.env` (só para tools
  CGU/sanções; ARP/CATMAT/PNCP funcionam sem credencial).
- Verificação: `hermes plugins list`, `hermes mcp list`, `hermes mcp test`.
- Para instalar em outra máquina: `hermes plugins install <repo>` ou symlink em
  `~/.hermes/plugins/` + `cd MCP_Compras && uv sync` + adicionar
  `compras-publicas` em `plugins.enabled`.

## Consulta ARP/CATMAT — receitas que funcionam

O campo `objeto` da ARP é genérico ("aquisição de material de informática") e o
CATMAT atrasa gerações de hardware — buscas textuais por modelo de GPU
(B200/B300) retornam 0. A rota confiável é **estrutural, via CATMAT**:

1. `compras_catmat_buscar {"termo":"SERVIDOR","codigo_grupo":70,"tamanho_pagina":100,"pagina":N}`
   paginado até `_total_paginas`. `termo` é OBRIGATÓRIO no schema mas o filtro
   textual upstream está quebrado — o servidor pagina o grupo inteiro e você
   filtra client-side (`descricaoItem` começa com "SERVIDOR" e contém "RACK").
   Grupo 70 = INFORMÁTICA; classe 7021 servidores, 7060 placas de vídeo.
   Servidores rack ficam em dezenas de códigos (451832-451847, 4599xx, ...);
   GPU avulsa = "PLACA CONTROLADORA VÍDEO" (464960 = acelerador 24 GB).
2. Para cada código: `compras_arp_itens_listar {"data_vigencia_inicial_min":...,"data_vigencia_inicial_max":...,
   "codigo_item":<catmat>,"tamanho_pagina":500}` — janela de início ≤ 365 dias;
   ARPs vigentes com início > 1 ano atrás exigem 2 janelas recuadas. Filtro
   "vigente hoje" = `dataVigenciaFinal[:10] >= hoje` e `not itemExcluido`.
3. `compras_arp_buscar_por_objeto` só serve para termos que REALMENTE aparecem
   no objeto (varre até 50 pgs × 500 = 25k atas; útil p/ 'notebook', 'uniformes';
   inútil p/ especificação técnica).
4. Filtro "órgão da União": o schema não traz esfera — heurística client-side
   sobre `nomeUnidadeGerenciadora` (excluir PREF, TRIBUNAL DE JUSTICA, GDF, ...)
   ou cruzar UASG com `compras_uasg_consultar`.

### ARP por número (ex.: "ARP 19/2025 do órgão X")
`compras_arp_listar(numero_ata_registro_preco="00019/2025", data_vigencia_inicial_min/max obrigatórios)`
— número com **zeros à esquerda** (5 dígitos + `/ANO`; "19/2025" retorna 0). O
filtro numérico é nacional: podem vir centenas de atas homônimas — varrer
`pagina=N` e filtrar client-side por `nomeOrgao`/`codigoUnidadeGerenciadora`.
O payload traz `numeroControlePncpAta` (`CNPJ-1-SEQ/ANO-00000N`, N = seq da ata)
→ deriva `sequencial` para `compras_pncp_contratacao_por_orgao` e
`compras_pncp_ata_arquivos`. NUNCA identificar a ata pelo número (homônimo
entre órgãos); sempre pelo `numeroControlePNCP`.

## Localizar contratações de uma UASG em um ano

`compras_contratacoes_14133_listar {"codigo_uasg":...}` frequentemente retorna
`"Recurso nao encontrado ..."` mesmo para UASG ativa — não é retry que resolve.
Rota que funciona:

1. `compras_uasg_consultar {"codigo_uasg":200342}` → `codigoOrgao`,
   `nomeUnidadeEspelho` (ex.: 200342 = DTI da PF/MJSP, órgão 30108, CNPJ
   do órgão-matriz 00394494000136 — PF/MJSP usa UM CNPJ para todas as UASGs).
2. `compras_pncp_contratacoes_publicacao {"cnpj":"<14 dígitos>","data_inicial":"20260101",
   "data_final":"...","pagina":N}` varrido até `_total_paginas` (datas `yyyyMMdd`).
   Cada linha traz `unidadeOrgao.codigoUnidade` = UASG → filtro client-side, e
   `numeroControlePncpCompra` = `CNPJ-1-SEQ/ANO`.
3. Para cada candidata: `compras_pncp_contratacao_por_orgao {cnpj, ano:"2026",
   sequencial:<int do controle>}` (objeto, valores, situação, `linkComprasGov`),
   depois os anexos para confirmar o tema — o objeto do PNCP às vezes é mais
   específico que o do Comprasnet.

Exemplo validado (09/2026): PF DTI 2026 → PE 90004/2026
(`00394494000136-1-000586/2026`), R$ 296,6 mi — TR com 5 tipos de servidor rack
em tabela Markdown após doc2md.

## Anexos da contratação (TR, Edital, ATA)

Os anexos NÃO estão na API `/api/consulta` (exige `chave-api-dadosabertos` e
retorna 404 p/ documentos). Ficam na API pública `https://pncp.gov.br/api/pncp`
— sem chave, sem captcha:

```
/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos[/{seqDoc}]               # Edital, TR, ETP
/v1/orgaos/{cnpj}/compras/{anoCompra}/{seqCompra}/atas/{ata}/arquivos   # ata + aditivos
/v1/orgaos/{cnpj}/contratos/{ano}/{seq}/arquivos                        # contratos
```

- No fork local virou 2 tools MCP: `compras_pncp_contratacao_arquivos` e
  `compras_pncp_ata_arquivos`. Detalhes de rotas em `references/pncp-arquivos-api.md`.
- Identificadores: `numeroControlePncpCompra` = `CNPJ14-1-SEQ/ANO`; sufixo de
  `numeroControlePncpAta` (`-000004/2024` → ata 4). `sequencial` na URL é SEM
  zeros à esquerda (`2101`), diferente do controle PNCP (`002101`).
- O arquivo "Edital" costuma vir como ZIP dentro de ZIP — `file` mostra "Zip
  archive data". Descompacte os 2 níveis antes de converter (doc2md
  `--engine anydoc`; Paddle só p/ escaneado).
- Aditivos de ata chegam como documentos extras tipo "Ata de Registro de
  Preços" — distinguir por `titulo`/`dataPublicacaoPncp`.
- A página SPA `pncp.gov.br/app/editais/...` é protegida por hCaptcha e fica
  "Carregando..." em browser headless — vá direto à API de arquivos.
- Lição: o CATMAT do item quase nunca reflete o TR (ARP 00103/2025 TRE-RN:
  CATMAT "acelerador 24 GB" escondia TR exigindo 48 GB GDDR6 / ~RTX 6000 Ada).
  Para spec técnica real, SEMPRE abrir o TR.

## Preços efetivamente contratados (atas da compra)

Quando `compras_arp_itens_listar` retorna 0 para a UASG gerenciadora (a base de
itens ARP do Dados Abertos NÃO indexa todas as UASGs — ex.: 200342/PF-DTI) e
`compras_montar_dossie_arp` dá `encontrada:false`, a rota é o PNCP público:

1. `GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/atas` → todas as atas
   (1 fornecedor = 1 ata; objetos divididos por lote).
2. PDF de cada ata: `GET .../atas/{seqAta}/arquivos/1` — traz FORNECEDOR, itens
   e tabela de preços registrados (unitário × qtd = total).
3. Converter com doc2md `--engine anydoc`; se "need OCR", fallback
   `pdftotext -layout` (salva a maioria das tabelas).
4. **Verificação cruzada**: soma dos VALOR TOTAL das atas ≈
   `valorTotalHomologado` da compra — sempre confira antes de reportar.
   Compare preço registrado vs `valorUnitarioEstimado` do TR.

## Contribuindo de volta ao upstream (fork → PR)

Receita para o clone vendorado (sem `.git`): ver `references/contribuir-pr.md`
(pontos-chave: `git apply -p2` do diff com prefixo `MCP_Compras/`, suíte
completa + `schema_snapshot.py` antes do push, e o `uv sync` silenciosamente
corrige drift do `uv.lock` — restaure o `uv.lock` do upstream antes do PR se
não for intencional).

## Pitfalls (verificados em produção)

- Especificações de GPU/CPU (B200, H100, VRAM) NÃO aparecem nem no `objeto` da
  ARP nem no CATMAT (teto do catálogo em 09/2026: "acelerador de GPU 48 GB",
  CATMAT 637988). A spec real só existe no TR do edital. Declare a limitação
  antes de concluir "não existe".
- `compras_catmat_buscar`: `termo` obrigatório mas filtro quebrado — combine
  com `codigo_grupo`/`codigo_classe` e filtre client-side (termo dummy "x" na
  varredura estrutural).
- Endpoints de ARP/itens exigem janela de vigência ≤ 365 dias.
- Chaves/tipos diferem entre tools (`sequencial` int vs `sequencialCompra`;
  `ano` string) — confira o `inputSchema` com `mcp_query.py _schema` antes de
  chamar tools novas.
- Campos como `numeroCompra`/`descricaoItem` podem vir `None` — use `.get()`.
- **Não encaminhe saída de rede para interpretador** (`... | python3`): dispara
  gate de aprovação e pode bloquear a cadeia. Redirecione para arquivo
  (`> /tmp/x.json`) e processe depois. Loops bash longos com URLs inline
  estouram o parser — escreva `/tmp/x.sh` via write_file e rode `bash /tmp/x.sh`.
- `tools/call` com argumento obrigatório faltante retorna texto de validação
  Pydantic no content (não erro JSON-RPC); tool que excepciona retorna
  `result.isError=true` — parseie com tolerância.
- Transporte: sem `PORT` no env o servidor fala stdio; handshake `initialize`
  → `notifications/initialized` → `tools/call`, newline-delimited JSON.
- Lote longo (>5 min): rode via `terminal(background=true, notify=true)`.
- Registro MCP: o do plugin (`mcp.json`) substitui o registro global antigo
  (`hermes mcp remove compras`); ferramentas em formato plugin usam o prefixo
  `mcp__compras-publicas__compras__`.

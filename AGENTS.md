# AGENTS.md — compras-publicas

Plugin Hermes (Agent Plugins v1) para pesquisa nos portais de compras e
contratações públicas do governo federal: **Compras.gov.br (Dados Abertos),
PNCP, Portal da Transparência/CGU e Comprasnet**.

Constituído pelo servidor **MCP_Compras** (~96 tools somente-leitura) +
**conjunto de skills** com receitas de pesquisa e pitfalls verificados.

## Estrutura

```
compras-publicas/
├── plugin.json                  # manifesto do plugin portável (Agent Plugins v1)
├── mcp.json                     # registra o MCP stdio quando o plugin está habilitado
├── skills/compras-publicas/     # skill de receitas (fonte canônica)
│   ├── SKILL.md                 #   receitas ARP/CATMAT/UASG/PNCP/anexos/preços + pitfalls
│   ├── references/              #   pncp-arquivos-api.md, contribuir-pr.md
│   └── scripts/mcp_query.py     #   cliente stdio JSON-RPC (uso fora de sessão Hermes)
├── skills/doc2md/               # skill de conversão doc→MD (uso dos anexos)
├── doc2md/                      # conversor vendorado (github.com/LeonardoDiasRR/doc2md)
│   ├── scripts/convert2md.py    #   CLI; wrapper bash só funciona em Linux
│   └── .venv/                   #   markitdown instalado; paddle/anydoc não (ver skill)
├── MCP_Compras/                 # servidor MCP vendorado (sem .git upstream)
│   ├── CLAUDE.md                #   convenções internas do servidor (SSoT, envelope, cache)
│   ├── .venv/                   #   uv sync; binário: .venv/bin/compras-mcp
│   └── .env                     #   TRANSPARENCIA_API_KEY (só tools CGU) — não commitado
├── scripts/                     # varreduras ad-hoc (scan_rack_arps.py, scan_gpu_mem.py)
└── resultados_*.json            # saídas de varreduras versionadas
```

## Instalação / ativação (esta máquina já está assim)

```bash
cd MCP_Compras && uv sync
ln -s ~/projetos/compras-publicas ~/.hermes/plugins/compras-publicas
hermes plugins enable compras-publicas
```

- O plugin registra o MCP automaticamente via `mcp.json` (nome interno
  `agent-plugin-compras-publicas-<digest>__compras`). **NÃO** registrar de novo
  com `hermes mcp add` — duplicaria ~96 tools.
- Skill também tem symlink `~/.hermes/skills/compras-publicas` →
  `skills/compras-publicas/` para permanecer no índice do system prompt
  (skills puramente de plugin ficam fora do índice).
- Tools MCP só aparecem em NOVA sessão do Hermes.

## Regras para agentes

1. **Conhecimento operacional mora na skill**, não aqui: receitas de consulta,
   pitfalls de API, fluxo de anexos PNCP e fluxo de PR upstream estão em
   `skills/compras-publicas/SKILL.md` (+ references/). Ao descobrir um pitfall
   novo, atualize a skill (e o symlink reflete automaticamente).
2. **MCP_Compras/ é fork de https://github.com/opedrosoares/MCP_Compras**
   (v0.3.15 + 2 tools locais de anexos PNCP). Alterações no servidor: seguir
   `MCP_Compras/CLAUDE.md` (descriptions SSoT em `schemas.py`, envelope padrão,
   registrar módulo em `server.py`) e a receita de PR em
   `skills/compras-publicas/references/contribuir-pr.md`. Portões antes de
   commit: `uv run pytest -q` + `uv run python scripts/schema_snapshot.py check`
   (+ atualizar `tests/test_tools_registry.py`, `manifest.json`, README quando
   mudar contagem de tools).
3. **Git**: repo próprio (remote `origin` = LeonardoDiasRR/compras-publicas,
   branch `main`). Commitar toda mudança; não commitar `.venv/`, `.env`,
   `dist/`. Ao extrair patch para PR upstream, o diff tem prefixo
   `MCP_Compras/` (usar `git apply -p2`).
4. **Sem credenciais no código**: única chave opcional é
   `TRANSPARENCIA_API_KEY` em `MCP_Compras/.env` (carregado pelo servidor;
   cwd do MCP já aponta para `MCP_Compras/`).
5. Consultas fora de sessão Hermes (scripts, cron): usar
   `skills/compras-publicas/scripts/mcp_query.py` —
   `python3 ... _list` | `_schema '{"names":[...]}'` | `<tool> '<json_args>'`.
6. Varreduras longas (>5 min): background com notify; nunca encaminhar saída
   de rede para interpretador (`| python3`) — salvar em arquivo e processar
   depois.
7. **Conversor doc2md** (`doc2md/`, vendorado de
   github.com/LeonardoDiasRR/doc2md): todo anexo de contratação/ARP (TR, edital,
   ata — PDF/docx/xlsx/zip) deve ser convertido para Markdown **antes** da
   leitura. No Windows: `doc2md/.venv/Scripts/python.exe
   doc2md/scripts/convert2md.py <arquivo> --engine markitdown -o <saida>.md`
   (paddle/anydoc não instalados aqui; PDF de banco tem camada de texto e o
   markitdown resolve; escaneado exigiria PaddleOCR — ver `skills/doc2md/SKILL.md`
   e `doc2md/references/install.md`).

## Verificação rápida

```bash
hermes plugins list | grep compras-publicas        # status enabled
python3 skills/compras-publicas/scripts/mcp_query.py _list | wc -l   # 96 tools
hermes plugins doctor .                            # validação do manifesto
```

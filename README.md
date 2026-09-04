# compras-publicas — Plugin Hermes

Plugin (Agent Plugins v1) para pesquisa nos portais de compras e contratações
públicas do governo federal (Compras.gov.br, PNCP, Portal da Transparência/CGU).

Constituído por:

- **MCP_Compras/** — servidor MCP https://github.com/opedrosoares/MCP_Compras
  (v0.3.15 vendorado + 2 tools locais de anexos PNCP = 96 tools; .git removido).
  Venv em `MCP_Compras/.venv` (`uv sync`).
- **skills/compras-publicas/** — skill única com receitas de pesquisa
  (ARP/CATMAT/UASG/PNCP/anexos/preços de atas), pitfalls verificados e
  referências (API pública de arquivos PNCP, fluxo de PR upstream).
- **plugin.json / mcp.json** — manifestos do plugin portável; registram o
  servidor MCP (stdio) automaticamente quando o plugin está habilitado.
- **scripts/** — varreduras CATMAT→ARP (scan_rack_arps.py, scan_gpu_mem.py) e
  consultas pontuais.

## Instalação / ativação

```bash
cd MCP_Compras && uv sync                                  # Python 3.11+
ln -s ~/projetos/compras-publicas ~/.hermes/plugins/compras-publicas
hermes plugins enable compras-publicas
```

O plugin registra o MCP automaticamente (novo nome interno
`agent-plugin-compras-publicas-*__compras`); tools MCP só aparecem em NOVA
sessão do Hermes. A skill também tem symlink em `~/.hermes/skills/compras-publicas`
para permanecer no índice do system prompt.

Opcional: `TRANSPARENCIA_API_KEY` em `MCP_Compras/.env`
(cadastro: https://api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email)
— necessário apenas para as tools de sanções CGU.

Verificação: `hermes plugins list`, `python3 skills/compras-publicas/scripts/mcp_query.py _list` (96 tools).

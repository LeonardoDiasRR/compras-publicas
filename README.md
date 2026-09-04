# compras-publicas

Consultas a compras públicas (Compras.gov.br / PNCP / Portal da Transparência) via MCP.

- `MCP_Compras/` — servidor MCP https://github.com/opedrosoares/MCP_Compras (v0.3.15, vendorado, .git removido)
- Instalado com `uv sync` em `MCP_Compras/.venv`
- Registrado no Hermes: `hermes mcp add compras --command .../MCP_Compras/.venv/bin/compras-mcp` (94 tools habilitadas)
- Opcional: chave do Portal da Transparência em MCP_Compras/.env (TRANSPARENCIA_API_KEY)

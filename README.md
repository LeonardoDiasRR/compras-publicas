# compras-publicas

Plugin de pesquisa em **compras e contratações públicas do governo federal**
(Compras.gov.br / PNCP / Portal da Transparência), constituído por dois
componentes:

1. **MCP_Compras** — servidor MCP ([opedrosoares/MCP_Compras](https://github.com/opedrosoares/MCP_Compras), FastMCP 2.x) vendorado e incrementado com 2 tools locais de anexos do PNCP: **96 tools somente-leitura** sobre as APIs públicas Dados Abertos Compras.gov.br, PNCP Consulta, Portal da Transparência/CGU (sanções CEIS/CNEP/CEAF) e rotas abertas do Comprasnet Contratos. Cobre ARPs, CATMAT/CATSER, contratações 14.133, planos anuais (PCA/PGC), preços praticados, fornecedores, UASGs/órgãos e indicadores.
2. **Skill `compras-publicas`** — conhecimento operacional destilado em receitas de pesquisa verificadas em produção: rota estrutural CATMAT→itens de ARP (busca textual por especificação de hardware **não** funciona no objeto da ARP), localização de contratações de uma UASG via PNCP, download de TR/edital/ata pela API pública de arquivos do PNCP (sem chave, sem captcha — o SPA `pncp.gov.br/app/editais` é protegido por hCaptcha), consolidação de preços efetivamente contratados (uma ata por fornecedor) e uma lista longa de pitfalls de API (janelas de vigência ≤ 365 dias, zeros à esquerda em números de ata, campos `None`, filtros quebrados upstream).

O campo `objeto` das ARPs é genérico e o CATMAT atrasa gerações de hardware: a skill documenta por que a rota confiável para especificação técnica real é **sempre abrir o Termo de Referência** nos anexos da compra — e como fazê-lo.

## Estrutura

```
compras-publicas/
├── plugin.json / mcp.json       # plugin portável Agent Plugins v1 (Hermes)
├── AGENTS.md                    # regras para agentes que operam o repositório
├── skills/compras-publicas/     # skill: SKILL.md + references/ + scripts/
│   └── scripts/mcp_query.py     #   cliente stdio JSON-RPC (funciona sem harness)
├── MCP_Compras/                 # servidor vendorado (sem .git); ver CLAUDE.md interno
└── scripts/                     # varreduras CATMAT→ARP prontas (rack, GPU)
```

## Pré-requisitos

- Python **3.11+** e [uv](https://docs.astral.sh/uv/)
- `cd MCP_Compras && uv sync` → cria o venv com o binário `MCP_Compras/.venv/bin/compras-mcp`
- Opcional: `TRANSPARENCIA_API_KEY` em `MCP_Compras/.env` — **apenas** para as tools de sanções do Portal da Transparência/CGU ([cadastro gratuito](https://api.portaldatransparencia.gov.br/api-de-dados/cadastrar-email)). Todo o resto (ARP, CATMAT, PNCP, preços) funciona sem credencial.

O servidor fala **stdio** por padrão (e HTTP em `0.0.0.0:$PORT` se `PORT` estiver no env). Nos exemplos abaixo, substitua `<ABS>` pelo caminho absoluto onde você clonou este repositório.

```bash
git clone https://github.com/LeonardoDiasRR/compras-publicas.git
cd compras-publicas/MCP_Compras && uv sync && cd ..
```

## Instalação nos harness

### Claude Code

```bash
# global (user scope)
claude mcp add compras -- <ABS>/MCP_Compras/.venv/bin/compras-mcp
# ou por projeto: crie .mcp.json na raiz do seu projeto
```

```json
{
  "mcpServers": {
    "compras": {
      "command": "<ABS>/MCP_Compras/.venv/bin/compras-mcp",
      "cwd": "<ABS>/MCP_Compras"
    }
  }
}
```

Skills: copie/symlink `skills/compras-publicas/` para `~/.claude/skills/`.

### Codex (CLI)

Em `~/.codex/config.toml`:

```toml
[mcp_servers.compras]
command = "<ABS>/MCP_Compras/.venv/bin/compras-mcp"
cwd = "<ABS>/MCP_Compras"
```

### OpenCode

Em `opencode.json` (raiz do projeto) ou `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "compras": {
      "type": "local",
      "command": ["<ABS>/MCP_Compras/.venv/bin/compras-mcp"],
      "cwd": "<ABS>/MCP_Compras",
      "enabled": true
    }
  }
}
```

### Hermes Agent

Instala-se como plugin portável (Agent Plugins v1) — o `mcp.json` do repositório registra o servidor automaticamente:

```bash
ln -s <ABS> ~/.hermes/plugins/compras-publicas
hermes plugins enable compras-publicas
```

Skills: symlink `skills/compras-publicas/` em `~/.hermes/skills/` para entrar no índice do system prompt. Tools MCP só aparecem em nova sessão. Ver `AGENTS.md`.

### DeepSeek Harness (dsh)

No config do harness, insira um bloco do cliente MCP stdio:

```yaml
- insert:
    - id: mcp-compras
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: compras
        transport: stdio
        command: <ABS>/MCP_Compras/.venv/bin/compras-mcp
        args: []
        env: {}
```

### Antigravity (IDE / CLI / SDK)

Config global compartilhada em `~/.gemini/config/mcp_config.json` (ou por workspace em `.agents/mcp_config.json`):

```json
{
  "mcpServers": {
    "compras": {
      "command": "<ABS>/MCP_Compras/.venv/bin/compras-mcp",
      "cwd": "<ABS>/MCP_Compras",
      "env": {}
    }
  }
}
```

Skills: copie `skills/compras-publicas/` para `~/.gemini/skills/` (formato SKILL.md padrão).

### Genérico (`.agents/` e demais clientes MCP)

`mcp.json` deste repositório já é o snippet padrão `mcpServers` (Agent Plugins v1) — funciona em qualquer cliente stdio-MCP que aceite o formato (Claude Desktop, Cursor, Cline, Zed, Antigravity workspace etc.). Para convenções `.agents/` (Antigravity SDK e harnesses que o seguem):

```
.seus-projeto/
└── .agents/
    ├── mcp_config.json    # conteúdo = mcp.json deste repo (ou cp .agents/mcp_config.json.example)
    └── skills/
        └── compras-publicas/   # cp -r skills/compras-publicas aqui
```

### Teste rápido (sem harness)

```bash
python3 skills/compras-publicas/scripts/mcp_query.py _list | wc -l      # 96 tools
python3 skills/compras-publicas/scripts/mcp_query.py \
  compras_arp_buscar_por_objeto '{"palavra_chave":"notebook","data_vigencia_final_min":"2026-09-01","data_vigencia_final_max":"2027-09-01"}'
```

## Limitações conhecidas

- Especificações de GPU/CPU de última geração não aparecem no `objeto` da ARP nem no CATMAT — confirme sempre no TR (a skill mostra o caminho).
- A API de itens ARP do Dados Abertos não indexa todas as UASGs; a rota alternativa é a API pública de arquivos do PNCP (uma ata por fornecedor, com validação pela soma ≈ `valorTotalHomologado`).
- Upstream ocasionalmente retorna 404/500 em `compras_contratacoes_14133_*` para UASGs ativas; use a rota PNCP documentada na skill.

## Upstream e Contribuição

Servidor: fork local de [opedrosoares/MCP_Compras](https://github.com/opedrosoares/MCP_Compras) (v0.3.15 + PR #1 de anexos PNCP). Convenções do servidor em `MCP_Compras/CLAUDE.md`; receita de PR a partir do clone vendorado em `skills/compras-publicas/references/contribuir-pr.md`.

Licença do servidor: ver `MCP_Compras/LICENSE`.

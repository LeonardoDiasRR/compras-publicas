# Contribuindo ao upstream opedrosoares/MCP_Compras a partir do clone vendorado

O clone local em `~/projetos/compras-publicas/MCP_Compras` perdeu o `.git` original
(vendorado) e vive dentro do repo pai `compras-publicas` — os paths do diff local têm
prefixo `MCP_Compras/`. Fluxo verificado (PR #1, set/2026):

```bash
# 1. Fork + clone limpo do fork
gh repo fork opedrosoares/MCP_Compras --clone=false
git clone https://github.com/LeonardoDiasRR/MCP_Compras.git /tmp/mcp_pr
cd /tmp/mcp_pr && git checkout -b feat/<nome>

# 2. Extrair SÓ o commit desejado do repo local e aplicar sem o prefixo
git -C ~/projetos/compras-publicas diff <sha_base> <sha_feat> -- MCP_Compras > /tmp/pr.patch
git apply --check -p2 /tmp/pr.patch && git apply -p2 /tmp/pr.patch

# 3. Portar os portões de qualidade do projeto ANTES do push
uv sync && uv run pytest -q                 # suíte completa (registro literal de tools exige
                                            # atualizar tests/test_tools_registry.py: nome no
                                            # bloco do módulo + contagem total)
uv run python scripts/schema_snapshot.py check   # falha se o snapshot commitado divergir;
                                                 # se adicionou tools: rode 'snapshot' e commite
# manifest.json (lista tools + descrição "N tools") e README (contagens) também são
# mantidos pelo autor — atualize os 3 junto ou o CI/drift reclama.

# 4. Push + PR cross-repo
git push https://x-access-token:$(gh auth token)@github.com/LeonardoDiasRR/MCP_Compras.git <branch>
gh pr create --repo opedrosoares/MCP_Compras --head LeonardoDiasRR:<branch> --base main ...
# Verificar de volta: gh pr view N --repo opedrosoares/MCP_Compras --json state,headRefOid,files
```

## Pitfalls
- **`uv sync` reescreve `uv.lock` silenciosamente** (corrige drift de versão do pacote
  vs pyproject) e a mudança entra no commit `-am`. Se o lock não é parte do escopo do
  PR: `git checkout HEAD~1 -- uv.lock` (ou `git show <upstream_sha>:uv.lock > uv.lock`),
  `git commit --amend`, force-push (force push exige aprovação do usuário).
- Não mexer em versão/CHANGELOG — release é do mantenedor (autor usa tags + CI que
  publica `compras.mcpb` e pacote PyPI).
- Commit com autor plausível para o fork: `-c user.email=leonardodiasrr@users.noreply.github.com`.
- O autor escreve em pt-BR; corpo do PR em português com tabela de tools, validação
  real ponta a ponta (ex.: download do TR de uma ARP específica) e exclusões honestas
  (o que a tool NÃO faz — ex.: download/unzip fica com o cliente).

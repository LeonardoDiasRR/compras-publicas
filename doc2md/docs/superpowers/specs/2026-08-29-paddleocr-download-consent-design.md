# Consentimento para download dos modelos PaddleOCR

## Objetivo

Deixar o download dos modelos locais do PaddleOCR explicitamente opt-in durante a instalação da skill, sem introduzir uma consulta interativa na primeira conversão.

## Escopo

- Atualizar `references/install.md` com uma etapa de confirmação antes do download.
- Documentar o comando mínimo que inicializa `PPStructureV3` e popula o cache local.
- Atualizar `SKILL.md` com um resumo do consentimento, do tamanho aproximado e do cache.
- Não alterar o script `convert2md`, que continuará sem interação.

## Fluxo

1. Instalar as dependências Python no `.venv` da skill.
2. Informar que os modelos do PaddleOCR ocupam aproximadamente 700 MB, exigem rede e são armazenados em `~/.paddlex`.
3. Perguntar ao usuário se deseja baixar os modelos agora.
4. Com confirmação, inicializar `PPStructureV3` para baixar e cachear os modelos.
5. Sem confirmação, não executar o download durante a instalação; documentar que uma conversão posterior de PDF pelo caminho padrão pode tentar baixá-los se o cache continuar ausente.

## Critérios de aceitação

- A documentação não inicia download sem consentimento durante a instalação e avisa sobre a tentativa automática possível em uma conversão posterior.
- O procedimento de aceite e recusa é executável e claro.
- Fica explícito que PDFs escaneados dependem do PaddleOCR, enquanto PDFs com camada de texto podem usar `anydoc` ou `markitdown`.
- Nenhum código de conversão é alterado.

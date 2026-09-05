# Instalação local (dentro da pasta da skill)

Todos os motores são instalados **dentro da skill** em
`~/.hermes/skills/doc2md/.venv` (Python 3.13.5). Nada foi instalado no
Python do sistema. Gerenciado com `uv` (já presente em ~/.local/bin/uv).

## Estado verificado em 2026-08-28

```
python 3.13.5 (uv venv)
paddlepaddle    3.2.2   (wheel cp313 muitaslinhas x86_64)  — ver "Por que 3.2.2"
paddleocr       3.7.0   (wheel py3-none-any)
paddlex         3.7.2   (+ extra [ocr] para PP-StructureV3)
firecrawl-anydoc 0.2.4  (wheel cp310-abi3 manylinux_2_17_x86_64)
markitdown      0.1.7   (extras: pdf, docx, pptx, xlsx)
```

Tamanho do venv: ~1,5 GB (paddlepaddle ~1 GB). Modelos de OCR do Paddle
(PP-OCRv5 + layout + tabelas, ~700 MB em ~/.paddlex) não fazem parte do venv;
o aquecimento consentido durante a instalação é o momento recomendado para
baixá-los e deixá-los em cache — requer rede.

### Por que paddlepaddle 3.2.2 (não 3.3.1)

paddlepaddle 3.3.1 (e todas as flags `FLAGS_use_mkldnn`, `FLAGS_enable_onednn`,
`FLAGS_enable_pir_api`) falha ao rodar o modelo de layout com
`NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support
[pir::ArrayAttribute<pir::DoubleAttribute>]` (oneDNN/PIR). O downgrade para
**3.2.2** roda o pipeline completo sem flags. Se um dia o 3.3.x for corrigido,
volte com `uv pip install paddlepaddle` e revalide com `scripts/self_test.sh`.

## Reprodução

```bash
SKILL=~/.hermes/skills/doc2md
uv venv --python 3.13 "$SKILL/.venv"
uv pip install --python "$SKILL/.venv/bin/python" \
  "markitdown[pdf,docx,pptx,xlsx]" firecrawl-anydoc
uv pip install --python "$SKILL/.venv/bin/python" paddlepaddle paddleocr
# extra obrigatório para o pipeline PP-StructureV3 (PDF -> markdown):
uv pip install --python "$SKILL/.venv/bin/python" "paddlex[ocr]==<versao do paddlex>"
```

## Download dos modelos do PaddleOCR

Instalar os pacotes não baixa os modelos. O aquecimento consentido durante a
instalação é o momento recomendado para baixar cerca de 700 MB para
`~/.paddlex`; portanto, o operador deve consultar o usuário antes de iniciar
esse download.

O fluxo abaixo recusa por padrão. Responda `y` ou `yes` para aceitar; qualquer
outra resposta recusa. Com aceite, a rede é necessária apenas se os modelos não
estiverem no cache local; depois, eles permanecem em `~/.paddlex`.

```bash
read -r -p "Baixar cerca de 700 MB de modelos do PaddleOCR agora? [y/N] " resposta
if [[ "$resposta" =~ ^([Yy]|[Yy][Ee][Ss])$ ]]; then
  "$SKILL/.venv/bin/python" - <<'PY'
from paddleocr import PPStructureV3

PPStructureV3(
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
)
PY
else
  echo "Download dos modelos recusado; nenhum download será feito agora."
fi
```

Se o usuário recusar, não baixe os modelos agora. Uma conversão posterior de
PDF pelo caminho padrão, que usa PaddleOCR, pode tentar baixá-los
automaticamente se `~/.paddlex` ainda não tiver os modelos. PDF escaneado exige
PaddleOCR; PDF com camada de texto pode usar `--engine anydoc` ou `--engine
markitdown` e não precisa desse download.

Observações:

- **paddleocr** é wheel puro (py3-none-any) e **paddlepaddle 3.3.1+** tem
  wheel cp313 — funciona em Python 3.13 (badge "3.8~3.12" do repo está
  defasado).
- **PP-StructureV3** exige o extra `paddlex[ocr]`; sem ele, a criação do
  pipeline falha com `DependencyError` ("A dependency error occurred during
  pipeline creation").
- **anydoc** tem wheel abi3 manylinux (cp310+) — instalado via PyPI
  (`firecrawl-anydoc`), sem Rust toolchain.
- **markitdown** extras mínimos: `[pdf,docx,pptx,xlsx]` (sem youtube/audio).
- Versões acima ficam estáveis; para atualizar, rode os mesmos comandos (uv
  resolve para a mais nova compatível) e revalide com `scripts/self_test.sh`.

## Onde está cada projeto

| Projeto (upstream)                 | Instalação local                          |
|------------------------------------|-------------------------------------------|
| github.com/PADDLEPADDLE/PADDLEOCR  | `.venv/lib/python3.13/site-packages/paddleocr` + `paddlex` |
| github.com/firecrawl/anydoc        | `.venv/.../site-packages/anydoc` (lib Rust via wheel abi3) |
| github.com/microsoft/markitdown    | `.venv/.../site-packages/markitdown`      |

Fixtures de teste: `github.com/firecrawl/anydoc/tests/fixtures/` (docx/pdf/xlsx/pptx reais).

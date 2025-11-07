# Etapa 02 — Estrutura inicial e scaffolding

## Organização do repositório
- Criado diretório `src/scriptum/` com módulos do compilador (`cli`, `driver`, `lexer`, `parser`, `ast`, `sema`, `codegen`) e subpacotes auxiliares (`regex`, `lexer`, etc.).
- Adicionados `scripts/` para automações (`build_afd.py`, `dev_commit.sh`) e `tests/fixtures/` para dados compartilhados da suíte.
- Configuração de empacotamento com `pyproject.toml`, documentação de topo em `README.md` e `lexer/tables.json` inicial para futura geração automática.
- Estrutura segue o pipeline descrito em `docs/wiki/01_gramatica.md`–`06_ir_codegen.md`, permitindo evolução incremental de cada fase.

## Dependências Python
- `click`: expõe a CLI (`scriptum --help`).
- `pytest`: base para a suíte de testes (instalado via extra `dev`).
- `typing-extensions`: compatibilidade de anotações avançadas durante a transição para Python 3.11+.

## Como testar e validar
- Instale o projeto em modo desenvolvimento:
  ```bash
  python -m venv .venv
  source .venv/bin/activate      # Windows: .venv\Scripts\activate
  uv sync --extra dev
  ```
- Rode a suíte (ainda vazia) para confirmar instalação:
  ```bash
  pytest
  ```
- Verifique a CLI:
  ```bash
  scriptum --help
  ```
- Próximas etapas adicionarão implementações reais para cada módulo e testes automatizados sobre `examples/`.

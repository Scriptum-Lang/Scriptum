# Changelog

## Unreleased

- Adicionado pipeline CI multiplataforma (Linux/macOS/Windows) com testes `uv run pytest` e artefatos buildados via `uv build`.
- Documentação atualizada para instalação com `uv`, `pip`, e `pipx` em todos os sistemas operacionais suportados.
- Criado `docs/wiki/99_release_template.md` com checklist de release e validação de pacotes `.whl`.
- Habilitada execução direta do pacote com `python -m scriptum` via novo módulo `scriptum/__main__.py`.

## 0.2.0 - 2025-10-24

- Implemented full lex/parse/sema/ir/codegen/run pipeline with CLI subcommands (`scriptum lex|parse|sema|ir|fmt|run`).
- Added structural IR interpreter plus semantics diagnostics carrying spans, line/column, and highlights.
- Introduced formatter/pretty-printer integration (`scriptum fmt`) and example programs + smoke tests.
- Added guardrails: regex builder alphabet/state/time limits and parser depth limit with configuration.
- Set up GitHub Actions CI with `ruff`, `black`, and `pytest`; added CHANGELOG and bumped version.

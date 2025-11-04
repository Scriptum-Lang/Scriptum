# Changelog

## 0.2.0 - 2025-10-24

- Implemented full lex/parse/sema/ir/codegen/run pipeline with CLI subcommands (`scriptum lex|parse|sema|ir|fmt|run`).
- Added structural IR interpreter plus semantics diagnostics carrying spans, line/column, and highlights.
- Introduced formatter/pretty-printer integration (`scriptum fmt`) and example programs + smoke tests.
- Added guardrails: regex builder alphabet/state/time limits and parser depth limit with configuration.
- Set up GitHub Actions CI with `ruff`, `black`, and `pytest`; added CHANGELOG and bumped version.

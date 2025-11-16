# Changelog

## [Unreleased]

_Sem mudanças registradas._

## [4.0.1] - 2025-11-07

### Added
- Documentacao oficial dos codigos de erro do lexer, parser, analisador semantico e runtime (novo capitulo `docs/wiki/13_error_reporting.md`) com exemplos reais do formato `ERRO [CODIGO]`.
- Guia consolidado de palavras-chave, operadores e funcoes builtin (`docs/wiki/14_keywords.md`), facilitando a consulta rapida da “tabela de comandos” da linguagem.

### Changed
- A funcao de entrada padrao passou a se chamar `principalis`, alinhando a sintaxe totalmente ao vocabulario em latim (CLI, exemplos e interprete).
- O REPL e o modo `scriptum -c` agora suspendem snippets dentro de `functio principalis`, preservando declaracoes e variaveis entre execucoes em linha.

## [4.0.0] - 2025-11-06

### Added
- Unified CLI error reports (codes, path/line hints, caret highlighting) across all commands.
- PyInstaller builds now run through `src/scriptum/__main__.py`, producing binaries aligned with the new Click CLI by default.

### Changed
- Version bumped to `4.0.0` to reflect the breaking CLI/tooling refresh completed since 0.3.1.
- Release tooling (`scriptum package`) always regenerates `build/scriptum.spec` pointing at the modern entry point unless a custom spec is supplied.
- Removed the legacy aliases (`scriptum lex|parse|sema|ir|compile|build-lexer`) and the `scriptum-classic` entry point; use `scriptum dev ...` instead.

### Fixed
- Inline execution via `scriptum -c` now wraps snippets automatically and surfaces structured diagnostics when inputs are invalid.

## [0.3.2] - 2025-11-05

### Added
- Nova hierarquia de comandos `scriptum` alinhada a CLIs modernas: `run`, `build`, `package`, `check`, `fmt`, `test`, `doc` e grupo `dev`.
- Execuções rápidas (`scriptum arquivo.stm`, `scriptum -c`, `scriptum -m`) e REPL experimental.
- Documentação servível via `scriptum doc build/serve` e suporte a `scriptum package` (PyInstaller).
- Alias de compatibilidade (`scriptum lex|parse|sema|ir|compile|build-lexer`) com avisos até a v0.4.0.

### Changed
- `scriptum dev <subcmd>` passou a agrupar ferramentas de inspeção (lex, AST, IR, tokens, build-lexer, bench).
- Scripts de smoke-test, README, wiki e exemplos foram atualizados para refletir o novo fluxo.
- Versão do projeto atualizada para `0.3.2`.
- CLI agora emite relatórios de erro padronizados com códigos/trechos para facilitar depuração.

### Fixed
- Mensagens de erros e diagnósticos agora são consistentes entre os novos comandos de alto nível e os utilitários em `dev`.

## [0.3.1] - 2025-11-05

### Added
- Standalone PyInstaller builds for Linux, macOS, and Windows (one-file executables).
- Installation scripts for Unix (`scripts/install.sh`) and Windows (`scripts/install.ps1`).
- Local smoke-test helpers (`scripts/smoke_local.sh`, `scripts/smoke_local.ps1`) covering lex/parse/sema.

### Changed
- Reworked CLI entrypoint with `--version`, `--help`, and dedicated subcommands wired through `scriptum.driver`.

### Fixed
- Packaged asset loading now respects embedded data regardless of the current working directory.

### Notes
- End users no longer need a local Python runtime; pre-built binaries ship with each GitHub release.
- Release artifacts include raw executables, platform archives, and `SHA256SUMS` for verification.

## [0.2.0] - 2025-10-24

- Implemented full lex/parse/sema/ir/codegen/run pipeline with CLI subcommands (`scriptum lex|parse|sema|ir|fmt|run`).
- Added structural IR interpreter plus semantics diagnostics carrying spans, line/column, and highlights.
- Introduced formatter/pretty-printer integration (`scriptum fmt`) and example programs and smoke tests.
- Added guardrails: regex builder alphabet/state/time limits and parser depth limit with configuration.
- Set up GitHub Actions CI with `ruff`, `black`, and `pytest`; added CHANGELOG and bumped version.

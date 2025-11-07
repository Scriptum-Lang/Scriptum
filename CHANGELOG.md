# Changelog

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

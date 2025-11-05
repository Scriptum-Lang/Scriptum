# Changelog

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

# Changelog

## [Unreleased]

_No changes recorded yet._

## [4.0.3] - 2025-12-01

### Added
- Backend de bytecode baseado em pilha (`scriptum.bytecode`) com VM própria (`BytecodeVM`), selecionável via `scriptum run --backend=bytecode`, além da listagem textual produzida por `scriptum build --backend bytecode --emit bytecode`. Novos testes (`tests/test_bytecode_backend.py`) abrangem loops, `frange/perge` e builtins como `summa`.
- Protótipo do backend LLVM em C++ composto por `scriptum::SimpleModuleEmitter`, bindings pybind11 (`scriptum_codegen_llvm_cpp_py`) e suíte GoogleTest (`cpp/llvm_codegen/tests/SimpleModuleTests.cpp`). O script `python scripts/build_cpp_backend.py` automatiza configuração, compilação e testes sempre que `LLVM_DIR`/`llvm-config` estiver disponível.
- Documentação do ecossistema de backends (README, wiki) detalhando `vm`, `bytecode`, `llvm` e `llvm-cpp`, novos requisitos e fluxos de fallback. `RELEASING.md` recebeu um checklist específico para v4.0.3.

### Changed
- O CLI aceita `--backend vm|bytecode|llvm|llvm-cpp` e variáveis `SCRIPTUM_BACKEND/SCRIPTUM_BACKEND_STRICT` agora contemplam os quatro modos. `_run_llvm_ir` centraliza o fluxo com `lli`, simplificando fallbacks.
- Processo de release automatizado requer atualização do changelog (seção 4.0.3), execução opcional de `scripts/build_cpp_backend.py` e validação do backend C++ antes de subir a tag.
- README/cpp/README refletem o novo script de build, instruções para `SCRIPTUM_LLVM_CPP_PATH` e orientam usuários sobre quando compilar o backend nativo.

### Fixed
- O otimizador local (`scriptum.optimizations.LocalOptimizer`) passa a realizar folding de `??`, `&&`, `||` mesmo quando apenas o operando esquerdo é literal, reduzindo IR redundante antes de qualquer backend.

## [4.0.2] - 2025-11-08

### Changed
- Unix installer (`scripts/install.sh`) now safely replaces a previous `scriptum` installation in `~/.local/bin` and, when another copy is found in a different directory, interactively offers to remove the older binary or keep it while recommending `PATH` adjustments.
- Installation documentation in `README.md` updated to explain behaviour when older versions are present on the system and the optional removal prompt.

## [4.0.1] - 2025-11-07

### Added
- Official documentation for lexer, parser, semantic analyser, and runtime error codes (new chapter `docs/wiki/13_error_reporting.md`) with real examples in the `ERRO [CODE]` format.
- Consolidated guide of keywords, operators, and builtin functions (`docs/wiki/14_keywords.md`), making it easier to consult the language's "command table".

### Changed
- The default entry function has been renamed to `principalis`, aligning the syntax fully with Latin vocabulary (CLI, examples, and interpreter).
- The REPL and `scriptum -c` now wrap snippets inside `functio principalis`, preserving declarations and variables across inline executions.

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
- New `scriptum` command hierarchy aligned with modern CLIs: `run`, `build`, `package`, `check`, `fmt`, `test`, `doc`, and the `dev` group.
- Fast execution flows (`scriptum file.stm`, `scriptum -c`, `scriptum -m`) and an experimental REPL.
- Documentation can now be built/served via `scriptum doc build/serve`, with `scriptum package` (PyInstaller) support.
- Compatibility aliases (`scriptum lex|parse|sema|ir|compile|build-lexer`) kept with warnings until v0.4.0.

### Changed
- `scriptum dev <subcmd>` now groups inspection tools (lex, AST, IR, tokens, build-lexer, bench).
- Smoke-test scripts, README, wiki, and examples updated to reflect the new flow.
- Project version bumped to `0.3.2`.
- CLI now emits standardised error reports with codes/snippets to simplify debugging.

### Fixed
- Error messages and diagnostics are now consistent between the new high-level commands and the utilities under `dev`.

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

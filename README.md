# Scriptum

![CI](https://github.com/Scriptum-Lang/Scriptum/actions/workflows/ci.yml/badge.svg)

Scriptum é uma linguagem didática inspirada em latim. Este repositório contém o compilador completo escrito em Rust, organizado como um workspace modular.

## Visão geral

- Lexer DFA (`crates/scriptum-lexer`).
- Parser Pratt/descida recursiva (`crates/scriptum-parser`).
- AST imutável com `NodeId` (`crates/scriptum-ast`).
- Verificador semântico/contextual (`crates/scriptum-types`).
- IR estruturada (`crates/scriptum-ir`).
- Pretty-printer/codegen (`crates/scriptum-codegen`).
- CLI unificada (`crates/scriptum-cli`).

Documentação completa em [`docs/wiki`](docs/wiki/00_index.md).

## Requisitos

- Rust 1.74+
- Linux/macOS/Windows

## Como compilar

```bash
cargo build --workspace
```

## Como testar

```bash
cargo test --workspace --all-features
```

## CLI `scriptum`

```bash
# listar tokens
cargo run -p scriptum-cli -- lex examples/basicos/hello.stm

# parsing + diagnósticos (texto ou --json)
cargo run -p scriptum-cli -- parse examples/basicos/hello.stm

# checar tipos
cargo run -p scriptum-cli -- check examples/basicos/hello.stm

# gerar código formatado
default_out=target/scriptum-out/hello.stm
cargo run -p scriptum-cli -- build examples/basicos/hello.stm --output "$default_out"

# formatar arquivo in-place
cargo run -p scriptum-cli -- fmt examples/basicos/hello.stm --write
```

## Scripts úteis

- `scripts/dev_commit.sh`: roda `fmt`, `clippy` (com `-D warnings`) e `test`.
- `scripts/run_all_tests.sh`: suíte de regressão estendida.

## Exemplos

A pasta [`examples/`](examples) contém programas agrupados por dificuldade e serve como base para testes dourados.

## Contribuindo

Leia [`docs/wiki/00_index.md`](docs/wiki/00_index.md) para entender o fluxo de contribuição. PRs são bem-vindos!

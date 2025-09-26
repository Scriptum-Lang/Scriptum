# Scriptum Compilador

Este monorepositório contém a implementação em Rust da linguagem Scriptum (`.stm`).

## Estrutura

O projeto é organizado como um workspace do Cargo com crates modulares correspondendo às
fases do compilador (lexer, parser, semântica, geração de código, runtime e CLI).

```
$ tree -L 2
compilador/
├── crates/        # bibliotecas reutilizáveis (AST, lexer, parser, ...)
├── examples/      # programas Scriptum demonstrativos (.stm)
├── fixtures/      # programas usados pelos testes automatizados
├── scripts/       # scripts utilitários (testes, build)
├── tests/         # testes de integração (cargo test)
└── tools/         # binários auxiliares (geração/validação de gramática)
```

## Requisitos

* Rust 1.75+ (edição 2021).
* `cargo` para compilação e testes.

## Uso rápido

```
cargo run -p scriptum-cli -- lex fixtures/programas_validos/hello_world.stm
```

Para executar toda a suíte:

```
./scripts/run_all_tests.sh
```

## Extensão `.stm`

* Código-fonte Scriptum: `text/x-scriptum`
* Especificações de teste: `text/x-scriptum` com sufixo `.spec.stm`
* Bytecode Scriptum: `application/x-scriptum-bc` (`.sbc`)

Consulte `docs/` para a especificação completa, arquitetura e guias de desenvolvimento.

# Scriptum Wiki

Bem-vindo ao hub de documentação oficial da linguagem **Scriptum** (`.stm`). Aqui você encontra a visão geral do projeto, as especificações formais e as diretrizes de contribuição.

## Conteúdo principal

1. [Gramática e sintaxe](01_gramatica.md)
2. [Léxico e tokens](02_lexico.md)
3. [Arquitetura do parser](03_parser.md)
4. [Árvore de Sintaxe Abstrata (AST)](04_ast.md)
5. [Tipos e análise semântica](05_tipos_semantica.md)
6. [IR, codegen e pipeline de build](06_ir_codegen.md)
7. [Roadmap e evoluções](99_roadmap.md)

## Arquitetura do repositório

```
.
├─ Cargo.toml (workspace)
├─ crates/
│  ├─ scriptum-ast
│  ├─ scriptum-lexer
│  ├─ scriptum-parser
│  ├─ scriptum-types
│  ├─ scriptum-ir
│  ├─ scriptum-codegen
│  └─ scriptum-cli
├─ docs/
│  ├─ wiki/
│  └─ diagrams/
├─ examples/
├─ scripts/
└─ README.md
```

Cada crate é autocontida, livre de dependências cíclicas e integrada via Cargo workspace. O CLI (`scriptum`) opera como entrypoint para lex, parse, AST, check, build e fmt.

## Convenções de contribuição

- **Rust 2021+** e `#![forbid(unsafe_code)]` em todas as crates.
- Use `cargo fmt`, `cargo clippy --deny warnings` e `cargo test --workspace` antes de enviar PRs (existe um script auxiliar em `scripts/dev_commit.sh`).
- Atualize a documentação quando alterar a gramática, AST ou fases do compilador. Cada mudança sintática deve refletir ajustes em `docs/wiki/01_gramatica.md` e `docs/wiki/02_lexico.md`.
- Diagnósticos devem citar spans (`scriptum_utils::Span`) e, quando possível, conter código de erro (`Txxx`, `Sxxx`).
- Tests unitários ficam em cada crate; testes integrados e *golden tests* usam `examples/`.

## Documentação legada

Materiais de versões anteriores (AFDs manuais, protótipos antigos etc.) foram movidos para [`docs/wiki/legacy/`](legacy/). Consulte-os apenas como referência histórica; o conteúdo desta wiki tem prioridade.

Boa leitura e bons commits! ☕️

# Guia de Desenvolvimento

## Pré-requisitos

* Rust 1.75+ com `rustfmt` e `clippy` instalados.
* Ferramentas opcionais: `cargo-criterion` para benchmarks, `graphviz` para
  geração de diagramas.

## Fluxo de trabalho

1. `cargo fmt` para manter o estilo.
2. `cargo clippy -- -D warnings` para lint.
3. `cargo test` para executar testes unitários e de integração.

Scripts auxiliares estão em `scripts/` e devem ser usados nos pipelines de CI.

## Contribuindo

* Priorize zero-copy e estruturas compactas.
* Documente `pub` APIs com exemplos de uso.
* Sempre atualize/adicione fixtures `.stm` ao criar novos recursos.

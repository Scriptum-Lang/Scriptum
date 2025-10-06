# Roadmap (99)

## Curto prazo

- Cobertura de testes: aumentar `examples/` com casos positivos/negativos.
- Implementar lint de variáveis não utilizadas (`scriptum-types`).
- Adicionar opção `--emit-ir` ao CLI para depuração.
- Concluir suporte a `=>` (lambdas expressão) na pretty-printing.

## Médio prazo

- Backend de bytecode + interpretador reescrito em cima do IR atual.
- Extensão da gramática para `switch/casus` e `match`.
- Modo *watch* no CLI (`scriptum check --watch`).
- Geração de documentação automática a partir da AST (ex.: `scriptum doc`).

## Longo prazo

- Servidor LSP (`crates/scriptum-lsp`) com *hover*, *go-to-definition* e diagnósticos incrementais.
- Otimizador de IR (propagação constante, DCE, SSA opcional).
- Backend LLVM/WASM opcional.
- Sistema de módulos multi-arquivo.

Sugestões são bem-vindas — abra uma issue no GitHub com a tag `enhancement` ou participe dos encontros quinzenais do projeto.

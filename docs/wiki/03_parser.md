# Parser e estratégia de análise

O parser (crate `scriptum-parser`) adota um estilo híbrido: um *Pratt parser* para expressões e descida recursiva estruturada para declarações. A linguagem permanece **G2** porque cada produção é livre de contexto. As principais decisões de projeto são:

- **Token stream imutável** (arena `SmallVec<Token>`), evitando realocações.
- **Recuperação de erros** simples com sincronização em `;` e `}`.
- **Spans preservados** em todos os nós da AST (`scriptum-ast`).
- **ID estável** (`NodeId`) gerado pelo parser para cada nó, útil para ferramentas (LSP) e caches.

## Precedência e associatividade

A tabela de precedência em [02_lexico.md](02_lexico.md) é implementada diretamente nas funções `parse_*`. `**` é associativo à direita; os demais operadores binários são à esquerda. `?:` é tratado após `??`, com `=` aplicando associação à direita.

## Resolução do *dangling else*

A regra `IfInstrucao` sempre consome o `aliter` mais próximo, graças ao uso de `parse_embedded_statement`. Não há ambiguidade na AST: o bloco de `aliter` é armazenado explicitamente.

## Generics e lambdas

`functio` suporta lista opcional de genéricos (`functio max<T>(...)`) tanto em funções quanto em lambdas. O parser aceita generics sintaticamente; a validação semântica fica a cargo da crate `scriptum-types`.

## Estrutura de erro

`ParseOutput` contém:

```rust
pub struct ParseOutput {
    pub module: Module,
    pub diagnostics: Vec<ParseError>,
}
```

`ParseError` inclui mensagem amigável e `Span`. Em modo `--json`, o CLI serializa esse objeto via `serde`.

## Normalização da AST

- `StringInterner` mantém símbolos únicos, evitando comparações custosas.
- `ExpressionKind::Assignment` cobre atribuições encadeadas (`a = b = c`).
- `StatementKind::Block` permite blocos inline (ex.: `si cond { ... } aliter { ... }`).

### Produções especiais

- **Objetos**: `structura { campo: expr, ... }`.
- **Arrays**: `[expr, expr, ...]`.
- **Lambdas**: `functio (params) => expr` ou `functio (params) { ... }`.

## Integração com outras fases

O parser retorna `Module` com todos os `NodeId` e `Span`. As fases seguintes consomem essa AST:

1. `scriptum-types` – checagem semântica/contextual.
2. `scriptum-ir::lower_module` – conversão para IR.
3. `scriptum-codegen::generate` – pretty-printer/bytecode.

Quando o parser acumula erros, as fases subsequentes podem optar por abortar ou prosseguir em modo tolerante (o CLI aborta na etapa atual).

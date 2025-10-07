# IR e codegen

As crates `scriptum-ir` e `scriptum-codegen` formam o backend atual.

## IR intermediária

- Representação estrutural (não SSA) com `ModuleIr`, `FunctionIr`, `IrStmt`, `IrExpr`.
- Preserva `Span` e `Symbol`, mantendo ligação com a AST original.
- Normaliza estruturas: `If` sempre possui vetores `then_branch`/`else_branch`, `While` armazena corpo como lista de `IrStmt`.
- Literais (`IrLiteral`) convertem diretamente os valores da AST.

### Lowering

`scriptum_ir::lower_module` percorre a AST e gera IR fiel, sem otimizações ainda. O objetivo é servir de alicerce para futuras transformações (ex.: eliminação de código morto, hoisting, SSA).

## Codegen / pretty printer

A função `scriptum_codegen::generate` devolve `CodegenOutput` com:

```rust
pub struct CodegenOutput {
    pub ir: ModuleIr,
    pub formatted: String,
}
```

O pretty-printer é idempotente (`scriptum fmt` roda duas vezes sem alterar o arquivo). Ele formata:

- Declarações globais (`mutabilis`/`constans`).
- Funções com bloco indentado.
- Expressões e operadores respeitando a precedência original.
- Literais com escapes preservados.

## Próximos passos

- Backend de bytecode reutilizando o IR.
- Otimizador (propagação constante, folding de `??`).
- Interface modular para futuros targets (LLVM, WASM).

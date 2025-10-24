# IR e codegen

As crates `scriptum-ir` e `scriptum-codegen` formam o backend atual.

## IR intermediária

- Representação estrutural (não SSA) com `ModuleIr`, `FunctionIr`, `IrStmt`, `IrExpr`.
- Preserva `Span` e os símbolos originais, mantendo ligação com a AST.
- Normaliza estruturas: `IrIf` expõe vetores `then_branch`/`else_branch`, `IrWhile` mantém o corpo como lista de `IrStmt`, `IrForIn` guarda o `IrForTarget` com mutabilidade e anotação.
- Literais (`IrLiteral`, `IrArrayLiteral`, `IrObjectLiteral`) carregam o valor e o lexema cru.
- Lambdas (`IrLambda`) preservam parâmetros, expressão-corpo ou bloco completo para posterior execução.

### Lowering

`scriptum_ir.lower_module(ast)` percorre a AST e gera um `ModuleIr` fiel, sem otimizações. Esse IR alimenta tanto o pretty-printer quanto o interpretador (`scriptum run`), servindo de base para futuras transformações (eliminação de código morto, SSA, etc.).

## Codegen / pretty-printer

A função `scriptum_codegen.generate(module)` aceita tanto um `nodes.Module` quanto um `ModuleIr`. Ela garante que exista um IR (executando o lowering quando necessário) e devolve um `CodegenOutput` com:

- `ir`: o `ModuleIr` produzido/reutilizado.
- `formatted`: string formatada e **idempotente** (rodar duas vezes não altera o arquivo).

O pretty-printer cobre:

- Declarações globais (`mutabilis`/`constans`) com espaçamentos consistentes.
- Funções com parâmetros, tipos de retorno e blocos identados.
- Estruturas de controle (`si`/`aliter`, `dum`, `pro`, `frange`, `perge`). 
- Arrays, `structura { ... }`, lambdas (`functio (...) => ...`) e chamadas/resolução de membros.
- Operadores com a mesma precedência e associatividade do parser (evitando parênteses redundantes).

O comando `scriptum fmt` usa `generate` para formatar arquivos ou STDIN, sobrescrevendo o arquivo apenas quando o conteúdo muda.

## Execução (mini VM)

O módulo `scriptum.ir.interpreter` implementa uma VM estrutural:

- Suporta `numerus`, `booleanum`, `nullum`, arrays, objetos e `??`, `?:`.
- Executa controle de fluxo (`si`, `dum`, `pro`) com `frange`/`perge`.
- Dá suporte a funções/lambdas com escopo léxico e parâmetros com default.

O comando `scriptum run` utiliza esse interpretador após passar por lex/parse/sema/IR, retornando o valor de `main()` (ou `nullum` caso não haja retorno explícito).

## Próximos passos

- Backend de bytecode reaproveitando o IR.
- Otimizador (propagação constante, folding de `??`).
- Interface modular para futuros targets (LLVM, WASM).

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

## Backend LLVM (experimental)

- Implementado em `scriptum.codegen.llvm` com saída textual pura (sem dependência de llvmlite). Cada valor Scriptum é rebaixado para `%scriptum.value`, um struct C descrito em `src/scriptum/runtime/runtime.h`.
- O runtime em C (`src/scriptum/runtime/llvm_rt.c`) oferece construtores, conversões e helpers para textos, arrays, objetos, opcionais e lambdas. Use `scripts/build_runtime.sh` para produzir `build/libscriptum_rt.{a,so}` (ou `.dll` no Windows) antes de integrar com `llvm-as`/`lli`.
- Testes rápidos:
  - `python -m pytest tests/test_runtime_llvm.py` compila o runtime em um diretório temporário e exercita os principais helpers via `ctypes`.
  - `python -m pytest tests/test_llvm_codegen.py` garante que o gerador emita IR contendo as chamadas corretas para o runtime (funções simples, `dum`, `pro in`, arrays, strings literais e `??`).
- Recursos já suportados no gerador: globais/funções, controle de fluxo (`si`, `dum`, `pro in`), arrays/objetos/textos literais, operadores aritméticos/comparações, `??` e retorna das funções via `scriptum_value`.
- `scriptum build --emit llvm --verify-llvm` e `scriptum dev llvm --verify` invocam `llvm-as` (quando disponível) para validar o IR gerado antes de exibi-lo.
- `scriptum run --backend=llvm` utiliza o runtime em C + `lli` (quando localizados) para executar `principalis()` nativamente, serializando o resultado em JSON. Caso `lli` ou o compilador C não estejam presentes, o comando volta para a VM estrutural e alerta o usuário.
- Builtins globais (`scribe`, `summa`, `numerus`, `textus`, etc.) agora s?o emitidos como chamadas diretas para helpers do runtime (`scriptum_rt_*`), preservando convers?es e IO id?nticos aos da VM.
- M?todos builtin (`array.*`, `textus.*`) tamb?m s?o emitidos como chamadas diretas para `scriptum_rt_array_*`/`scriptum_rt_text_*`, preservando as mesmas muta??es e convers?es esperadas pela VM.
- Recursos ainda pendentes nesta fase: integra??o mais profunda da CLI com `lli` para execu??o e uma su?te ampliada de regress?es (snapshots) em `tests/backend_llvm/`.

### Requisitos de ferramentas

- **Compilador C** (`cc`, `clang` ou `gcc`): usado para gerar `libscriptum_rt` on-demand. Defina a variável `CC` se precisar de um binário customizado.
- **Ferramentas LLVM**:
  - `llvm-as` (ou `LLVM_AS=/caminho/para/llvm-as`) para `--verify-llvm`.
  - `lli` (ou `LLI=/caminho/para/lli`) para executar `scriptum run --backend=llvm`/`SCRIPTUM_BACKEND=llvm`.
- Ausências são tratadas com mensagens informativas e fallback automático para a VM.

## Execução (mini VM)

O módulo `scriptum.ir.interpreter` implementa uma VM estrutural:

- Suporta `numerus`, `booleanum`, `nullum`, arrays, objetos e `??`, `?:`.
- Executa controle de fluxo (`si`, `dum`, `pro`) com `frange`/`perge`.
- Dá suporte a funções/lambdas com escopo léxico e parâmetros com default.

O comando `scriptum run` utiliza esse interpretador após passar por lex/parse/sema/IR, retornando o valor de `principalis()` (ou `nullum` caso não haja retorno explícito).


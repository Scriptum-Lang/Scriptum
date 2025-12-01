# LLVM Codegen (C++) – Plano de Implementação

> **Status:** planejamento aprovado. O backend textual atual continua ativo; este documento descreve o novo backend em C++/LLVM IR que partirá da AST/tabela de tipos já construídas em Python.

## Objetivo geral

Implementar uma etapa de geração de código em C++ que, recebendo a AST anotada e a análise semântica (tabela de símbolos + tipos), produza um `llvm::Module` pronto para ser otimizado (`opt`) ou executado (`lli`, JIT, `llc`). A interface exposta ao restante do compilador será inicializada a partir de bindings (pybind11 ou CLI) em uma fase posterior.

Referências diretas:

1. [LLVM “Kaleidoscope” tutorial](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/index.html)
2. [LLIR user guide](https://llir.github.io/document/user-guide/basic/)
3. [Packt – Introducing LLVM IR](https://www.packtpub.com/en-us/learning/how-to-tutorials/introducing-llvm-intermediate-representation)
4. [Talk: My First Language Frontend w/ LLVM](https://www.youtube.com/watch?v=oE0dTkxJSXU)

## Estado atual (Dez/2025)

- SimpleModuleEmitter gera llvm::Module para fun??es que retornam literais ou a soma de dois literais (add). Os testes vivem em cpp/llvm_codegen/tests/SimpleModuleTests.cpp (GoogleTest).
- indings.cpp exp?e emit_module(module_ir, module_name) via pybind11 (scriptum_codegen_llvm_cpp_py). O binding percorre o ModuleIr real vindo do Python, extrai o ?ltimo IrReturn e, se a express?o for compat?vel, invoca o emissor.
- O script python scripts/build_cpp_backend.py prepara o ambiente (cmake + LLVM), compila scriptum_codegen_llvm_cpp_py.* e executa os testes automaticamente (pode ser invocado com --skip-tests).
- scriptum run --backend=llvm-cpp j? usa o binding; o CLI recai para a VM quando o m?dulo n?o estiver dispon?vel e respeita SCRIPTUM_LLVM_CPP_PATH para localizar builds customizados.
- Roadmap curto: suportar vari?veis locais/parametriza??o, emitir sub/mul/div, encadear blocos e incorporar o runtime oficial (scriptum_value).

## Camadas

1. **Visitor da AST**
   - Define interfaces `ExprVisitor`, `StmtVisitor`, `FunctionVisitor`. Cada nó da AST terá `accept(*visitor)`.
   - Responsável por orquestrar a travessia e invocar helpers de emissão.
2. **Contexto de geração (`CodegenContext`)**
   - Contém `llvm::LLVMContext`, `llvm::Module`, `llvm::IRBuilder<>` e referências a tabelas de símbolos/tipos.
   - Armazena pilhas de escopos (`std::vector<std::unordered_map<std::string, llvm::Value*>>`) e blocos de controle para `break`/`continue`.
   - Provê utilitários para gerar nomes únicos, empilhar escopos, registrar funções, criar blocos.
3. **Camada de emissão (`Emitter`)**
   - Encapsula chamadas diretas à API LLVM (criação de módulos, basic blocks, GEP, casts).
   - Traduz tipos da linguagem em `llvm::Type*` e garante casts corretos (sext/zext/sitofp etc.).
4. **Otimização local**
   - Constant folding e simplificações algébricas antes de materializar instruções. Serve como “pré-pass” antes dos pipelines oficiais.

Cada camada será testada isoladamente e poderá ser mockada em testes unitários.

## Visitor / percursos

- `visitLiteral`, `visitIdentifier`, `visitBinary`, `visitUnary`, `visitCall`, `visitArrayAccess`, `visitMemberAccess` retornam `llvm::Value*`.
- `visitIf`, `visitWhile`, `visitFor`, `visitReturn`, `visitVarDecl`, `visitAssignment` manipulam blocos e atualizam o contexto.
- `visitFunctionDecl` cria `llvm::Function`, parâmetros, bloco de entrada e visita o corpo.

## Contexto

Estrutura `CodegenContext` (ver `cpp/llvm_codegen/include/scriptum/CodegenContext.h`):

- `llvm::LLVMContext`, `std::unique_ptr<llvm::Module>`, `llvm::IRBuilder<> builder`.
- Pilha de escopos (`ScopeStack`), pilha de loops (`LoopStack`), mapa de funções.
- Acesso à tabela de tipos (proveremos interface em C++ mais adiante; por ora, usamos stubs).
- Helpers `pushScope()`, `popScope()`, `lookupSymbol()`, `registerSymbol()`, `createEntryAlloca()` etc.

## Geração de expressões/comandos

- Expressões binárias/unárias: recursivas, escolhendo instrução (`CreateAdd`/`CreateFAdd`, `CreateICmpEQ`/`CreateFCmpOEQ` etc.) com base no tipo semântico.
- Literais: `llvm::ConstantInt`, `llvm::ConstantFP`, `ConstantStruct` quando necessário.
- Chamadas: resolve `llvm::Function*`, gera argumentos, usa `builder.CreateCall`.
- Arrays/Structs: `CreateGEP` seguido de `CreateLoad`/`CreateStore` conforme contexto.
- Controle de fluxo: `CreateCondBr`, `CreateBr`, blocos `then/else/merge`, loops com blocos `cond/body/end` e suporte a `break`/`continue` via `LoopStack`.
- `return`: `CreateRet`/`CreateRetVoid` assegurando término de bloco.

## Funções/variáveis

- Funções globais: `llvm::Function::Create` com linkage consistente com a análise semântica.
- Variáveis globais: `llvm::GlobalVariable`, `ExternalLinkage` para símbolos exportados, inicializadores default.
- Variáveis locais: padrão alloca-no-entry + `mem2reg` (posteriormente). Podem ser marcadas com `IRBuilder::CreateAlloca` e armazenadas em `ScopeStack`.

## Tipos/conversões

- Mapa central em `Emitter::toLLVMType(SemanticType)` que retorna `llvm::Type*`.
- Casts inseridos automaticamente em operações quando operandos divergirem (widening, int↔float, ponteiros).

## Otimizações locais

- `FoldConstants` (arith/logical).
- Simplificações (`x + 0`, `x * 1`, `if true`, `if false`). Implementadas em `optimizer/LocalOptimizer.{h,cpp}` dentro do módulo.

## Testes e validação

- Testes unitários C++ (GoogleTest) exercendo visitantes e garantindo que o IR gerado corresponde a snapshots (`llvm::verifyModule`).
- Integração com `llvm-as`, `lli`, `llc` para smoke tests.

## Integração

- O wrapper Python chamará a biblioteca C++ (via pybind11) em etapa futura; por ora, focamos em produzir uma biblioteca independente (`libscriptum_codegen_llvm_cpp`).

## Fases sugeridas

1. **Sessão 1** – Planejamento (mapeamento de runtime, requisitos de lambdas/builtins/métodos). ✅
2. **Sessão 2** – Implementar lambdas (structs de captura + `scriptum_lambda_*`).
3. **Sessão 3** – Mapear builtins globais para símbolos de runtime.
4. **Sessão 4** – Métodos (`array.*`, `textus.*`) e receivers.
5. **Sessão 5** – Testes, otimizações e integração final com a pipeline Python.

Este documento deve ser mantido junto com o progresso do backend C++.

# LLVM Backend – Arquitetura de Runtime

> **Escopo desta entrega:** manter a arquitetura do runtime/gerador textual LLVM. O runtime C (`src/scriptum/runtime/llvm_rt.c`) e o gerador (`src/scriptum/codegen/llvm/`) já estão implementados de forma experimental; este documento alinha estruturas, contratos e próximos passos.

## Objetivos

## Estado atual (Dez/2025)

- **Bytecode**: um backend experimental (scriptum.bytecode) gera instru??es de pilha (PUSH_CONST, LOAD_GLOBAL, JUMP_IF_FALSE, CALL, etc.) a partir do ModuleIr e as executa em BytecodeVM. O backend compartilha os mesmos builtins da VM estrutural e j? suporta literais, dum/range/perge, atribui??es e chamadas simples. Os testes vivem em 	ests/test_bytecode_backend.py e o CLI aceita --backend=bytecode.
- **LLVM textual**: permanece como descrito nas se??es anteriores, com snapshots em 	ests/backend_llvm/ e valida??o via llvm-as. O script scripts/build_runtime.sh continua compilando src/scriptum/runtime/llvm_rt.c.
- **LLVM C++**: adicionamos um emissor m?nimo em C++ (scriptum::SimpleModuleEmitter) e bindings em pybind11 (scriptum_codegen_llvm_cpp_py). O emissor aceita fun??es que retornam literais ou somas de literais e gera llvm::Module validado com llvm::verifyModule. Os testes do GoogleTest moram em cpp/llvm_codegen/tests/SimpleModuleTests.cpp. O script python scripts/build_cpp_backend.py gera o m?dulo compartilhado e registra os testes; a CLI importa automaticamente o binding e volta para a VM quando ele n?o estiver dispon?vel (SCRIPTUM_LLVM_CPP_PATH permite apontar para builds customizados).

- Manter uma representação uniforme (`scriptum_value`) que possa armazenar qualquer valor da linguagem e trafegar entre LLVM IR e o runtime C.
- Determinar estruturas auxiliares para tipos compostos (textos, arrays, objetos, lambdas, opcionais).
- Definir a API mínima exposta pelo runtime (alocação, destruição, conversões, helpers de arrays/objetos/strings) e a convenção de chamada (C ABI padrão).
- Alinhar as responsabilidades entre o gerador LLVM e o runtime: o gerador apenas empacota/desempacota valores e delega operações complexas ao runtime.

## Representação de Valores

Todos os valores trafegam como `struct scriptum_value`, definido em `src/scriptum/runtime/runtime.h` e implementado em `src/scriptum/runtime/llvm_rt.c` (compilado via `scripts/build_runtime.sh`). A estrutura contém:

```c
typedef enum scriptum_value_kind {
    SCRIPTUM_VALUE_UNDEFINED = 0,
    SCRIPTUM_VALUE_NUMBER,
    SCRIPTUM_VALUE_BOOLEAN,
    SCRIPTUM_VALUE_TEXT,
    SCRIPTUM_VALUE_ARRAY,
    SCRIPTUM_VALUE_OBJECT,
    SCRIPTUM_VALUE_LAMBDA,
    SCRIPTUM_VALUE_OPTIONAL,
    SCRIPTUM_VALUE_NULL,
} scriptum_value_kind;

typedef struct scriptum_value {
    scriptum_value_kind kind;
    double number;
    int32_t boolean;
    uint32_t _reserved;
    void *payload;
} scriptum_value;
```

- `kind` indica o tipo lógico.
- `number` e `boolean` share o mesmo layout, permitindo recuperar rapidamente numerus/booleanum sem indirections.
- `payload` aponta para structs heap quando necessário (textos, arrays, objetos, lambdas, opcionais). Para valores numéricos/booleanos, `payload` é `NULL`.

### Textos

```c
typedef struct scriptum_text {
    uint64_t ref_count;
    uint64_t length;
    char *data; /* buffer UTF-8, sem terminador obrigatório */
} scriptum_text;
```

O runtime oferece `scriptum_text_new(const char *data, uint64_t len)` e garante ref-counting (incrementa ao clonar, libera quando `ref_count == 0`). Concatenação, comparação e extração do buffer UTF-8 usam helpers (`scriptum_text_concat`, `scriptum_text_compare`, `scriptum_text_release`).

### Arrays

```c
typedef struct scriptum_array {
    uint64_t ref_count;
    uint64_t length;
    uint64_t capacity;
    scriptum_value *items;
} scriptum_array;
```

Helpers implementados:
- `scriptum_array_new(uint64_t capacity)`
- `scriptum_array_push(scriptum_array *, scriptum_value value)`
- `scriptum_array_get(scriptum_array *, uint64_t index, scriptum_value *out)`
- `scriptum_array_set(...)`
- `scriptum_array_len(...)`

### Objetos

```c
typedef struct scriptum_object_entry {
    scriptum_text *key;
    scriptum_value value;
} scriptum_object_entry;

typedef struct scriptum_object {
    uint64_t ref_count;
    uint64_t length;
    uint64_t capacity;
    scriptum_object_entry *entries;
} scriptum_object;
```

Representação simples baseada em vetor ordenado (inserções fazem busca linear). Helpers:
- `scriptum_object_new(void)`
- `scriptum_object_set(scriptum_object *, scriptum_text *key, scriptum_value value)`
- `scriptum_object_get(...)`

### Lambdas

```c
typedef scriptum_value (*scriptum_lambda_entry)(void *closure, scriptum_value *args, uint64_t argc);

typedef struct scriptum_lambda {
    uint64_t ref_count;
    scriptum_lambda_entry entry;
    void *closure;
} scriptum_lambda;
```

O gerador LLVM passará a criar structs de captura, passar o ponteiro como `closure` e deixar o runtime tratar ref-count. Chamadas indiretas serão emitidas como chamadas diretas ao `entry` (pendente nesta etapa).

### Valores Opcionais

```c
typedef struct scriptum_optional {
    uint64_t ref_count;
    uint8_t is_present;
    scriptum_value value;
} scriptum_optional;
```

Como opcionais podem conter qualquer valor, reusam `scriptum_value` internamente e mantêm ref-count próprio. O runtime oferece `scriptum_optional_new` e `scriptum_optional_or_else`.

## API exposta

O gerador textual declara todas as funções de `runtime.h` no preâmbulo LLVM e invoca diretamente os helpers do runtime. Os grupos principais:

- **Alocação/gerenciamento:** `scriptum_alloc`, `scriptum_release` e os pares `*_retain/*_release` para textos, arrays, objetos, opcional e lambda.
- **Construtores:** `scriptum_value_number/boolean/text/array/object/lambda/optional/null`, garantindo que cada literal ou resultado seja materializado como `scriptum_value`.
- **Conversões:** `scriptum_value_as_number`, `scriptum_value_as_boolean`, além de `scriptum_value_expect_{text,array,object,lambda,optional}` utilizados durante `pro in`, operadores e futuros builtins.
- **Strings/arrays/objetos:** `scriptum_text_new/concat/compare`, `scriptum_array_new/push/get/set/len`, `scriptum_object_new/set/get` — já consumidos pelo gerador para literais e loops.
- **Opcionais:** `scriptum_optional_new` e `scriptum_optional_or_else`, que serão vinculados quando `??`/`?:` forem estendidos para valores opcionais concretos.
- **Lambdas:** `scriptum_lambda_new` e `scriptum_lambda_call`, planejados para a próxima etapa (captura/execução).
- **Integração CLI:** `scriptum_rt_dump` serializa um `scriptum_value` em JSON e grava no caminho apontado por `SCRIPTUM_LLVM_RESULT`, permitindo que `scriptum run --backend=llvm` capture o resultado ao invocar `lli`.

### Checklist para lambdas/builtins/métodos

- **Runtime já disponível**
  - `scriptum_lambda_new`, `scriptum_lambda_retain/release`, `scriptum_lambda_call`.
  - Helpers globais (`scriptum_rt_scribe`, `scriptum_rt_summa`, `scriptum_rt_textus`, etc.) e métodos (`scriptum_array_push`, `scriptum_text_concat`, ...).
- **Lacunas**
  - Integra??o CLI (`scriptum run --backend=llvm`) com `lli`/fallbacks ainda precisa de ajustes para produzir diagn?sticos consistentes e evitar recompila??es redundantes.
  - Revisitar conven??es de reten??o/libera??o quando closures capturam valores complexos (principalmente com futuros objetos/opcionais).

### AST/IR (estado atual)

- `IrLambda` (ver `ir/ir.py`) contém parâmetros, corpo e `return_annotation`.
- `IrCall` mantém `binding` para builtins/métodos resolvidos pela análise semântica.
- `IrMemberAccess` preserva `binding` de método quando aplicável.
- Não é necessário alterar o lowering — o gerador apenas precisa consumir esses metadados.

### Plano de geração

1. **Lambdas**
   - Para cada literal: gerar `struct` com capturas, função `@lambda.N` com assinatura `scriptum_value (i8*, %scriptum.value*, i64)` e instanciar via `scriptum_lambda_new`.
   - Capturas armazenam `scriptum_value` (ou ponteiros nativos quando aplicável).
2. **Builtins globais**
   - Criar tabela `nome -> símbolo runtime` e emitir `call` direta (com box/unbox) quando `IrCall.binding` apontar para builtin.
3. **Métodos**
   - Mapear `receiver.kind + método` para helper correspondente (`scriptum_array_push`, `scriptum_text_split`, ...).
   - Receiver passa como primeiro argumento (ponteiro) seguido dos demais parâmetros.

### Sess?o 3 ? Builtins globais

- Declaramos todos os helpers `scriptum_rt_*` no runtime (`runtime.h`/`llvm_rt.c`) e passamos a export?-los no pre?mbulo textual, facilitando a liga??o direta no IR.
- `scriptum.codegen.llvm.generator` detecta `IrCall` cujo alvo ? um builtin global, derrama os argumentos em um buffer tempor?rio e chama o helper correspondente (`@scriptum_rt_summa`, `@scriptum_rt_textus`, ...).
- A su?te em `tests/backend_llvm/` ganhou o fixture `builtins.stm` e snapshots atualizados; `tests/test_llvm_codegen.py` agora valida explicitamente a emiss?o de `@scriptum_rt_*`.

### Sess?o 4 ? M?todos builtin

- Runtime passou a expor helpers `scriptum_rt_array_*` e `scriptum_rt_text_*` cobrindo `adde/exime/extende/inserta/remove/purga` e `divide/coniunge/substitue/ad_minusculas/ad_maiusculas/abscinde`.
- O gerador detecta `IrMemberAccess` com binding para builtin e injeta as chamadas adequadas, convertendo o receiver para `%scriptum.array*` ou `%scriptum.text*` antes de montar o buffer de argumentos.
- Novos testes exercitam esses caminhos (`tests/test_llvm_codegen.py`) e o snapshot `tests/backend_llvm/snapshots/methods.ll` garante estabilidade do IR.



### Sessao 5 ? Selecao de backend e regress?es

- `scriptum run` e `scriptum build` agora aceitam `--backend vm|llvm` e `--strict-backend`, alem das variaveis `SCRIPTUM_BACKEND`/`SCRIPTUM_BACKEND_STRICT`, permitindo definir o modo padrao de execucao/geracao e decidir quando falhar em vez de voltar para a VM.
- `scriptum build` ajusta o artefato padrao conforme o backend (formato legivel para `vm`, IR textual para `llvm`) e bloqueia combinacoes incoerentes, evitando colisao de artefatos.
- README, docs e TODO foram atualizados com instrucoes de selecao de backend e os testes de CLI cobrem os novos caminhos (incluindo fallback e modo estrito).

Todas as funções usam a convenção C padrão (`cdecl`). No IR textual, os `declare` correspondentes vivem em `scriptum.codegen.llvm.runtime.RUNTIME_PREAMBLE`.

## Pr?ximos Passos

1. **Integra??o CLI:** finalizar `scriptum run --backend=llvm` com execu??o via `lli`, mensagens de erro claras e caching do runtime.
2. **Su?te dedicada:** criar `tests/backend_llvm/` com snapshots normalizados e execu??es comparando sa?da com a VM para arrays, strings, `??`, lambdas e objetos.
3. **Documenta??o cont?nua:** manter README/wiki sincronizados com novos componentes, incluindo troubleshooting (`llvm-as`/`lli` ausentes) e fluxos de build/execu??o.

Este documento deve permanecer alinhado com `runtime/runtime.h` e `scriptum.codegen.llvm.runtime` sempre que novos módulos/estruturas forem adicionados.

## Backend LLVM C++ (prot?tipo)

- O binding exp?e emit_module(module_ir, module_name) em scriptum_codegen_llvm_cpp_py. Ele recebe o ModuleIr Python diretamente (via pybind11), inspeciona o corpo das fun??es e converte retornos literais ou somas simples em scriptum::SimpleFunction.
- O emissor atual (SimpleModuleEmitter) gera fun??es double () contendo apenas 
et double <const> ou add entre dois literais. llvm::verifyModule ? executado automaticamente e erros retornam para o Python como LLVMCPPBackendError (o CLI os converte em diagn?sticos amig?veis).
- O roadmap inclui suportar vari?veis, par?metros, condicionais e liga??es de runtime; abra novas issues referenciando esta se??o quando expandir o escopo.
- Para desenvolver localmente, rode python scripts/build_cpp_backend.py (opcionalmente --skip-tests) e exporte SCRIPTUM_LLVM_CPP_PATH se o m?dulo resultante n?o estiver em cpp/llvm_codegen/build.


# Scriptum LLVM Runtime

Este diretório contém a implementação em C utilizada pelo backend LLVM textual. Ele expõe a API declarada em `runtime.h`, oferecendo:

- Representação unificada de valores (`scriptum_value`), com suporte a numerus, booleanum, textos, arrays, objetos, opcionais e lambdas com captura.
- Estruturas heap com contagem de referências (textos, arrays, objetos, lambdas, opcionais).
- Helpers para conversões, concatenação de textos, manipulação de arrays/objetos, construção de opcionais e chamadas de lambdas.

## Build

O runtime pode ser compilado em forma de biblioteca estática ou compartilhada. O script abaixo utiliza `cc` (ou o compilador definido via `CC`) para gerar os artefatos dentro de `build/`:

```bash
scripts/build_runtime.sh
```

Ele produz:

- `build/llvm_rt.o` — objeto compilado de `llvm_rt.c`.
- `build/libscriptum_rt.a` — biblioteca estática.
- `build/libscriptum_rt.so` (ou `.dll` no Windows) — biblioteca compartilhada.

Altere `CFLAGS`/`LDFLAGS` no ambiente caso precise de opções extras (por exemplo, `-fsanitize`).

## Testes

Há testes unitários básicos (`tests/test_runtime_llvm.py`) que:

1. Compilam o runtime para uma biblioteca compartilhada em diretório temporário.
2. Exercitam via `ctypes` as principais operações (numerus/booleanum, textos, arrays) para validar o contrato público.

Os testes exigem um compilador C acessível (`cc`, `clang` ou `gcc`). Caso não esteja disponível, eles são ignorados.

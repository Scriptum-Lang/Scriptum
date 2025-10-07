# Etapa 10 — Documentação final e guia de uso

## Módulos entregues
- `lexer`: geração de DFAs, CLI (`build-lexer`, `lex`) e tokens/AST correspondentes.
- `parser`: Pratt + descida recursiva (`parse --dump-ast`).
- `sema`: tabela de símbolos, tipos básicos e analisador com diagnósticos.
- `scripts`: utilitários (`build_afd.py`).
- `tests`: smoke/regressão para parser e semântica.

## Exemplos de uso
```bash
scriptum version
scriptum build-lexer
scriptum lex examples/ok/basicos/variaveis.stm
scriptum parse examples/ok/intermediarios/classes.stm --dump-ast
```

## Roadmap próximo
- Conectar análise semântica à CLI (comando dedicado ou integrado a `run`).
- Implementar geração de IR e codegen (`06_ir_codegen.md`).
- Expandir testes negativos, enforcement de tipos em chamadas e arrays.
- Planejar backend bytecode/interpretador.

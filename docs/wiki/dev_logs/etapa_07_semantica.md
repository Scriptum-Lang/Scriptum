# Etapa 07 — Análise semântica e tipos

## Estratégia
- Implementada `SymbolTable` com escopos aninhados, símbolos contendo tipo e mutabilidade.
- Tipos primitivos mapeados a `TypeKind`; suporte a opcionais (`?`), `quodlibet` como supertipo e compatibilidade básica (ex.: `nullum` para opcionais).
- `SemanticAnalyzer` percorre AST: declarações, expressões, atribuições e retornos. Usa inferência simples para literais, identificadores, operações aritméticas e atribuições.

## Diagnósticos
- Erros coletados como `SemanticDiagnostic` com mensagem e `Span` associado.
- Exemplos: tentativa de atribuir `textus` para variável `numerus`, retorno incompatível, uso de identificador não declarado.

## Como testar
- Regenerar e analisar:
  ```bash
  pytest -q scriptum/tests/test_semantics.py
  ```
- Rodar sobre exemplo negativo:
  ```bash
  scriptum parse examples/err/negativos/tipo_incompativel.stm
  ```
  (Verificar diagnósticos via `SemanticAnalyzer`).

# Etapa 06 � Parser e gram�tica

## Hierarquia de preced�ncia
- Seguimos a tabela de `docs/wiki/02_lexico.md`: atribui��o (`=`) < condicional (`? :`) < coalesc�ncia (`??`) < `||` < `&&` < igualdade (`==`, `!=`, `===`, `!==`) < compara��o (`>`, `<`, `>=`, `<=`) < soma/subtra��o < produto (`*`, `/`, `%`) < exponencia��o (`**`) < postfix (`()`, `[]`, `.`) geridos como liga��es de maior preced�ncia.
- Pratt parser calcula *binding power* a partir de `parser/precedence.py`, garantindo associatividade correta (`**` e `=` � direita, demais � esquerda).

## Statements estruturais
- `si/aliter`: parse recursivo garante o `aliter` mais interno, compondo n�s `IfStatement` com ramos opcionais.
- `dum`: n� `WhileStatement` avalia condi��o antes de consumir o corpo.
- `pro`: suporta cabe�alho `mutabilis/constans` com tipo opcional ou forma direta `numerus saldo in expr`, produzindo `ForStatement` com `ForTarget` tipado.
- `redde`: aceita retorno vazio ou express�o, sempre exigindo `;`. Comandos `frange`/`perge` tamb�m demarcam `;` obrigat�rio.

## Testes e uso
- Parser validado com exemplos intermedi�rios/avan�ados (`tests/test_parser_examples.py`), garantindo que estruturas `while`, `if/else` e chamadas estejam presentes na AST.
- CLI atualizada:
  ```bash
  scriptum build-lexer
  scriptum parse examples/ok/intermediarios/classes.stm --dump-ast
  ```
- Suite completa:
  ```bash
  pytest -q tests/test_parser_examples.py
  ```

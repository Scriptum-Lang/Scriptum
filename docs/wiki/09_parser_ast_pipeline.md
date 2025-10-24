# Parser e AST passo a passo

Este documento apresenta o fluxo completo da fase de parsing de Scriptum, desde a entrada de tokens ate a producao da `nodes.Module`.

## 1. Entrada de tokens

- O parser instancia internamente um `ScriptumLexer` (`parser/parser.py`, construtor) e chama `tokenize` em `ScriptumParser.parse`.
- Os tokens carregam `TokenKind`, `lexeme`, `Span` e metadados adicionais que podem ser usados em mensagens de erro.
- `ParserConfig` permite ajustar comportamentos (por exemplo, `allow_lambda_shortcut` para lambdas com corpo expressao).

## 2. Estrutura principal (`ScriptumParser`)

- Mantem uma lista `self._tokens` e um indice atual (`self._index`).
- `self._node_counter` gera `node_id` unicos para a AST.
- Metodos utilitarios privados (`_peek`, `_advance`, `_match_symbol`, `_check_keyword` etc.) fornecem operacoes de leitura com lookahead e validacoes.

## 3. Declaracoes de alto nivel

- `_parse_declaration` decide entre:
  - `functio`: `_parse_function_declaration`, que consome nome, parametros, tipo de retorno opcional (`->`) e um bloco.
  - `mutabilis` / `constans`: `_parse_variable_declaration`, com suporte a anotacao de tipo opcional e inicializador.
  - Caso contrario, delega a `_parse_statement` e exige que o resultado seja uma `Declaration`.
- `parse` acumula todas as declaracoes em `nodes.Module`.

## 4. Declaracoes auxiliares e blocos

- `_parse_parameters` cria `nodes.Parameter` para cada entrada, anotando `default_value` quando `=` aparece.
- `_parse_block_statement` consome `{ ... }` e devolve `nodes.BlockStatement` com uma lista de `Statement`.
- Estruturas de controle (`if`, `while`, `for`, `redde`, `frange`, `perge`) possuem funcoes dedicadas que constroem os nos correspondentes em `ast/nodes.py`.

## 5. Expressao com Pratt parser

- `binding_powers` (`parser/precedence.py`) mapeia operadores para `left` e `right binding power`, definindo precedencia e associatividade.
- `_parse_expression_bp` aplica o algoritmo de Pratt:
  1. L� um prefixo (literais, identificadores, prefixos unarios, lambdas).
  2. Enquanto o binding power do operador encontrado for maior que o limite atual, consome o operador e parseia o operando direito.
- Operadores suportados incluem: atribuicao, condicional ternario (`?:`), nullish (`??`), logicos, comparacoes, aritmeticos, exponenciacao e posfixos (chamada `()`, acesso `.`, indexacao `[]`).
- Lambdas (`functio (...) => expr` ou bloco) reutilizam a logica de parametros e blocos, produzindo `nodes.LambdaExpression`.

## 6. Construcao da AST

- Todos os nos derivam de `nodes.Node` e guardam:
  - `node_id` sequencial (gerado por `_next_id`).
  - `span` com inicio/fim absolutos no texto (combinados via `_combine_spans`).
- `nodes` define tipos especificos para declaracoes (`FunctionDeclaration`, `VariableDeclaration`), instrucoes (`IfStatement`, `WhileStatement`, `ReturnStatement` etc.) e expressoes.
- Literais recebem `value` (resultado da conversao no lexer) e `raw` (lexema original) via `nodes.Literal`.

## 7. Tratamento de erros

- Erros de sintaxe geram `ParseError`, derivado de `errors.CompilerError`.
- Metodos `_consume_*` exibem mensagens amigaveis indicando o token esperado e a posicao (`Span`), facilitando a depuracao.
- O parser ainda nao implementa recuperacao avancada, mas a estrutura permite sincronizacao futura (por exemplo, ao encontrar `;` ou `}`).

Com este pipeline, a transicao de texto para AST se mantem deterministica e previsivel, fornecendo informacoes ricas (spans, ids, metadados) para as fases seguintes.

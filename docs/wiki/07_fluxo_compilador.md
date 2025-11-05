# Fluxo completo do compilador Scriptum

Este documento descreve, etapa por etapa, como o projeto Scriptum transforma um arquivo `.stm` em estruturas internas prontas para analise, geracao de codigo ou outras ferramentas. Cada fase aponta para os modulos Python correspondentes dentro de `src/scriptum`.

## 1. Entrada de texto

- O `CompilerDriver` (`scriptum/driver.py`) recebe um `pathlib.Path` opcional e carrega o conteudo com `text.SourceFile`.
- `SourceFile` (`scriptum/text.py`) empacota o texto cru e oferece spans (`Span`) usados por todas as fases seguintes para diagnosticos consistentes.

## 2. Geracao da tabela do lexer (etapa offline)

Embora o driver ainda nao exponha o *build* automatico, o repositorio inclui o pipeline que converte especificacoes de tokens em uma tabela DFA serializada (`lexer/tables.json`):

1. `lexer/spec.py` descreve cada token via `TokenPattern` (regex, prioridade, flag `ignore`, tipo).
2. `regex/parser.py` analisa a regex textual para uma AST de nos definidos em `regex/ast.py`.
3. `regex/nfa.py` aplica a construcao de Thompson e monta um AFN parametrizado pela AST.
4. `regex/dfa.py` determiniza e minimiza o AFN, preservando metadados de aceitacao.
5. `regex/builder.py` orquestra os passos acima, reordena estados e devolve tabelas prontas para serializacao.
6. `lexer/generator.py` chama o *builder* e grava `lexer/tables.json`, utilizado pelo lexer em tempo de execucao.

## 3. Tokenizacao

- `ScriptumLexer` (`lexer/lexer.py`) carrega `tables.json` uma vez (cache em `_TABLES_CACHE`) e percorre o codigo fonte caractere a caractere, seguindo as transicoes do DFA.
- Ao encontrar um estado de aceitacao, cria `tokens.Token` com:
  - `TokenKind` de `tokens.py` (`IDENTIFIER`, `KEYWORD`, `NUMBER_LITERAL` etc.).
  - `Span` calculado sobre o buffer original.
  - `value` derivado de literais numericos ou de string.
- Palavras reservadas (lista `KEYWORDS`) promovem identificadores para `TokenKind.KEYWORD`.
- Tokens com `ignore=True` (espacos e comentarios) sao descartados quando `LexerConfig.skip_whitespace` esta habilitado.

## 4. Construacao da AST

- O `ScriptumParser` (`parser/parser.py`) consome a lista de tokens:
  - Declaracoes de topo sao analisadas por funcoes dedicadas (`_parse_function_declaration`, `_parse_variable_declaration`).
  - Expressoes usam um Pratt parser parametrizado por `binding_powers` (`parser/precedence.py`), garantindo precedencia e associatividade corretas.
  - Cada no AST eh instanciado a partir de `ast/nodes.py` com `node_id` incremental e span correspondente.
- O resultado final eh um `nodes.Module` contendo todas as declaracoes.

## 5. Analise semantica

- `SemanticAnalyzer` (`sema/analyzer.py`) percorre a AST:
  - Mantem uma tabela de simbolos em pilha (`sema/symbols.py`) para escopos aninhados.
  - Converte anotacoes de tipo em objetos `Type` (`sema/types.py`) e valida atribuicoes, retornos e uso de identificadores.
  - Acumula `SemanticDiagnostic` com mensagens e spans quando encontra erros.

## 6. IR, pretty-printer e execução

- `ir/lowering.py` converte `nodes.Module` em `ModuleIr`, preservando spans e estrutura.
- `codegen/generate.py` garante o lowering (quando necessário) e chama `codegen/emitter.py`, produzindo `formatted` + `ModuleIr`.
- `ir/interpreter.py` executa o IR resultante (mini VM). O comando `scriptum run` percorre lex/parse/sema/IR e chama o interpretador, retornando o valor de `main()`.
- `scriptum fmt` usa o mesmo pipeline até o IR e grava o código formatado somente quando há mudanças.

## 7. Resumo do pipeline

```
SourceFile -> Lexer (DFA tables) -> Tokens
          -> Parser (Pratt + descida) -> AST (nodes.Module)
          -> SemanticAnalyzer -> Diagnostics + tipos decorados
          -> IR lowering -> ModuleIr
          -> Codegen (pretty-printer) / Interpreter (scriptum run)
```

Use esta visao como guia ao navegar pelo repositorio ou implementar novas features. Cada etapa publica APIs claras para facilitar testes isolados.

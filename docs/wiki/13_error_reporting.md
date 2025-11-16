# Diagnóstico e códigos de erro

O Scriptum exibe toda falha do pipeline no mesmo formato, independente do estágio (lexer, parser, análise semântica, IR ou runtime):

```
ERRO [PAR105] Expected ';' after variable declaration. Found '}'.
--> caminho/do/arquivo.stm:4:29
        mutabilis numerus x = 1 }
                               ^
```

- A primeira linha contém o prefixo `ERRO`, o código e uma mensagem objetiva.
- A segunda linha (`-->`) aponta o caminho lógico + linha + coluna.
- As duas linhas seguintes mostram o trecho do código com acento circunflexo (`^`) exatamente sobre o `Span` problemático.

Essa formatação é produzida por `ErrorReport` (`src/scriptum/reporting.py`) e reaproveitada em todos os comandos do CLI (`scriptum run`, `scriptum check`, `scriptum dev ...` etc.).

## Catálogo de códigos

Os códigos sempre têm três letras que identificam o subsistema seguidas de três dígitos que agrupam erros por categoria.

### Lexer (`LEX`)

| Código | Origem | Condição típica | Referência |
| --- | --- | --- | --- |
| `LEX001` | `ScriptumLexer._lex_error` | Caractere não reconhecido pelo DFA. | `src/scriptum/lexer/lexer.py:166` |
| `LEX002` | `ScriptumLexer._unterminated_block_comment` | Comentário `/* ...` sem `*/`. | `src/scriptum/lexer/lexer.py:173` |

### Parser (`PAR`)

| Código | Categoria | Exemplos |
| --- | --- | --- |
| `PAR100` | Construções proibidas no topo do arquivo. | Qualquer statement fora de declaração (`src/scriptum/parser/parser.py:139`). |
| `PAR101` | Limite de profundidade excedido. | Expressões com aninhamento > `ParserConfig.max_depth`. |
| `PAR102` | Token inesperado durante leitura prefixa. | Símbolo não suportado para iniciar expressão. |
| `PAR103` | Ausência de anotação de tipo. | Falha ao consumir `numerus`, `textus` etc. em declarações. |
| `PAR104` | Consumo genérico (`_consume`). | Mensagens “Expected … Found …” para tipos de token. |
| `PAR105` | Consumo de símbolos (`;`, `)`, `]` …). | Mais comum em declarações sem `;`. |
| `PAR106` | Palavras-chave obrigatórias. | `functio`, `mutabilis`, `constans` etc. |
| `PAR5xx` | Conversão LL(1) auxiliar. | Falhas internas ao reconstruir AST aritmética (`PAR500`–`PAR503`). |

### Semântica (`S` / `T`)

Os diagnósticos semânticos já utilizavam códigos antes desta refatoração. Seguem os agrupamentos documentados em `src/scriptum/sema/analyzer.py`:

| Prefixo | Descrição | Exemplo |
| --- | --- | --- |
| `S1xx` | Símbolos e escopos | `S110` para redeclaração de identificadores. |
| `S2xx` | Controle de fluxo | `S200` para `redde` fora de função. |
| `T2xx` | Verificações de tipo em geral | `T200` para atribuições incompatíveis. |
| `T3xx` | Validação de chamadas/builtins | `T301` erros de aridade/assinatura em `applica`, `longitudo` etc. |

Esses códigos também são convertidos para `ErrorReport`, preservando o span capturado pelo analisador.

### Runtime e IR (`IR`)

| Código | Origem | Condição | Referência |
| --- | --- | --- | --- |
| `IR001`–`IR003` | `Environment` | Declaração duplicada, atribuição em `constans`, nome inexistente. | `src/scriptum/ir/interpreter.py:47-80` |
| `IR010`–`IR011` | `Interpreter.execute` | `main` ausente ou não chamável. | `src/scriptum/ir/interpreter.py:150-165` |
| `IR020`–`IR021` | Binding de parâmetros | Aridade incorreta em funções/lambdas. | `src/scriptum/ir/interpreter.py:210-230` |
| `IR030`–`IR041` | Execução de statements/expressões | `break` fora de laço, operadores não suportados, atribuições inválidas. | `src/scriptum/ir/interpreter.py:258-335` |
| `IR050`–`IR061` | Acesso a membros, indexação, chamadas | Objetos não indexáveis, `call` em não-função etc. | `src/scriptum/ir/interpreter.py:347-383` |
| `IR070`–`IR080` | Binários e iteráveis | Operadores desconhecidos ou uso de `pro` em valores não iteráveis. | `src/scriptum/ir/interpreter.py:418-452` |
| `IR200`–`IR239` | Builtins e métodos | Aridade, tipos ou pré-condições específicas de `ambitus`, `longitudo`, `divide`, `exime`, `remove` etc. | `src/scriptum/builtins.py` |

## Exemplos rápidos

- `examples/err/lex_unexpected_character.stm` provoca `LEX001` ao inserir `@` dentro do corpo da função.
- `examples/err/lex_unterminated_comment.stm` ilustra `LEX002`.
- `examples/err/parse_missing_semicolon.stm` gera `PAR105`.
- `examples/err/parse_unexpected_keyword.stm` gera `PAR102` ao tentar usar a palavra-chave `si` como expressão.
- `examples/err/type_mismatch.stm` mostra `S120` (atribuição em `constans`) logo antes de `T200`.
- `examples/err/builtin_longitudo.stm` demonstra `T301` (checagem semântica) enquanto `examples/err/runtime_ambitus_zero_step.stm` aciona `IR234` apenas em tempo de execução.
- `examples/err/runtime_exime_empty.stm` dispara `IR237` e `examples/err/runtime_divide_empty_separator.stm` aciona `IR239`.
- `examples/err/builtin_applica_predicate.stm` cobre `T301`, e o mesmo arquivo causa `IR200` se for executado ignorando a correção semântica.

Execute qualquer exemplo com `scriptum run arquivo.stm` ou `scriptum check arquivo.stm --json` para visualizar o relatório padronizado e verificar a tabela acima.

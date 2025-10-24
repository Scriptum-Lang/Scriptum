# AFN e AFD no lexer Scriptum

Este guia resume como o pipeline lexico emprega automatos finitos nao deterministico (AFN) e deterministico (AFD), destacando o papel de cada estrutura dentro do codigo fonte do projeto.

## Visao geral

```
Regex (lexer/spec.py)
      │ parse
      ▼
AST (regex/parser.py + regex/ast.py)
      │ Thompson
      ▼
AFN (regex/nfa.py)
      │ determinize + minimize
      ▼
AFD (regex/dfa.py)
      │ serializar
      ▼
tables.json → ScriptumLexer (lexer/lexer.py)
```

## AFN: construcao via Thompson

- Implementado em `regex/nfa.py` pela classe `ThompsonBuilder`.
- Cada regra de `TokenPattern` gera fragmentos que se conectam com transicoes epsilon, permitindo multiplos caminhos para o mesmo prefixo.
- Caracteristicas principais:
  - Estados possuem `epsilon` (set) e `transitions` mapeando simbolos para conjuntos de estados.
  - Construtores auxiliares cuidam de sequencia (`_build_sequence`), alternancia (`_build_alternation`), repeticao (`_build_repetition`) e classes de caracteres (`_literal_fragment`).
  - Varios estados de aceitacao coexistem; o payload `AcceptInfo` eh anexado somente ao estado final do fragmento da regra.
- O AFN facilita composicao direta das regex, mas nao e usado em tempo de execucao por ser custoso percorrer varios estados simultaneamente.

## AFD: determinizacao e minimizacao

- `regex/dfa.py` converte o AFN em um conjunto de estados deterministico via `determinize`.
  - Cada estado do AFD representa o fecho-epsilon de um subconjunto de estados do AFN.
  - A funcao `_select_accepting` escolhe a regra vencedora com base em prioridade e ordem de insercao.
- `DFA.make_total` adiciona um estado poco quando falta transicao para algum simbolo, garantindo comportamento previsivel.
- `DFA.minimize` aplica Hopcroft para mesclar estados equivalentes, reduzindo o tamanho da tabela final.
- O resultado final e consumido por `regex/builder.py`, que reindexa estados, transforma simbolos em strings e produz as estruturas usadas em `tables.json`.

## Comparativo rapido

| Aspecto              | AFN (regex/nfa.py)                             | AFD (regex/dfa.py)                                |
| -------------------- | ---------------------------------------------- | ------------------------------------------------ |
| Tipo de transicao    | Pode ter multiplas transicoes por simbolo ou ε | Exatamente uma transicao por simbolo (apos make_total) |
| Uso principal        | Etapa intermediaria de construcao              | Tabela final utilizada pelo lexer                |
| Complexidade runtime | Exige rastrear conjuntos de estados            | Caminho unico, custo linear no comprimento do lexema |
| Otimizacao           | Nenhuma (estrutura direta)                     | Minimizado e completado                          |
| Payload de aceitacao | Guardado por estado final adicionado ao AFN    | Herdado do AFN e resolvido por prioridade        |

## Onde tudo se integra

- `lexer/generator.py` chama `AutomataBuilder.build`, acessa `result.dfa` (AFD minimizado) e grava `tables.json`.
- `lexer/lexer.py` carrega `tables.json`, reconstrui `DFAState` deterministico e tokeniza o codigo fonte sem nunca tocar no AFN original.
- Caso novas regras sejam adicionadas em `lexer/spec.py`, basta regenerar as tabelas para que o AFN/AFD seja atualizado automaticamente.

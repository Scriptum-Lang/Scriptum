# Pipeline do lexer Scriptum

Este guia descreve passo a passo como o lexer de Scriptum nasce da especificacao declarativa ate produzir tokens prontos para o parser.

## 1. Especificacao declarativa (`lexer/spec.py`)

- `TokenPattern` agrupa `name`, `kind`, `pattern`, `priority` e `ignore`.
- A lista `TOKEN_PATTERNS` inclui regras baseadas em regex para espacos, comentarios, literais, identificadores e depois adiciona operadores, pontuacao e delimitadores a partir de `tokens.py`.
- `TOKEN_SPECS` normaliza cada regra em uma tupla `(nome, regex, prioridade, ignore, kind)` usada pelo gerador de tabelas.

## 2. Parser de regex (`regex/parser.py`)

- `RegexParser` implementa descida recursiva com suporte a alternancia, concatenacao, grupos, classes de caracteres, quantificadores (`*`, `+`, `?`, `{m,n}`) e escapes hexadecimais.
- Cada padrao textual vira uma AST usando os nos de `regex/ast.py` (`Literal`, `Sequence`, `Alternation`, `Repeat`, `CharacterClass` etc.).
- Erros sintaticos geram `RegexSyntaxError` com posicao precisa.

## 3. Construcao do AFN (`regex/nfa.py`)

- `ThompsonBuilder` percorre a AST e produz fragmentos conectados por transicoes epsilon.
- Cada literal adiciona uma aresta para um novo estado (`_literal_fragment`), enquanto:
  - `Sequence` concatena fragmentos.
  - `Alternation` cria um estado inicial compartilhado com transicoes epsilon para cada opcao, convergindo em um estado final unico.
  - `Repeat` trata quantidades minimas, maximas, opcional (`_make_optional`) e estrela (`_make_star`).
- O resultado e um `NFA` com `states`, `start_state`, `accepting` (payload com `AcceptInfo`) e `alphabet`.

## 4. Determinizacao e minimizacao (`regex/dfa.py`)

- `determinize` aplica o metodo de subconjuntos:
  - Calcula o fecho-epsilon do estado inicial.
  - Cria um `DFAState` para cada conjunto distinto de estados do AFN.
  - Seleciona o payload de aceitacao com maior prioridade (desempate pelo `order` da regra original).
- `DFA.make_total` garante que cada estado possua transicao para todo simbolo conhecido (cria um estado poço se necessario).
- `DFA.minimize` usa o algoritmo de Hopcroft para agrupar estados equivalentes, mantendo a semantica do DFA.

## 5. Serializacao (`regex/builder.py` e `lexer/generator.py`)

- `AutomataBuilder.build` processa todas as regras, gera o DFA minimizado e devolve:
  - `dfa`: automato deterministico pronto.
  - `alphabet`: conjunto de codigos inteiros usados nas transicoes.
  - `accept_entries`: lista de `AcceptInfo` com o metadado de cada estado final.
- `build_tables_from_specs` reindexa os estados (ordenacao BFS opcional), converte simbolos para strings (`_symbol_to_str`) e monta o dicionario final com chaves `states`, `start`, `trans`, `finals` e os mapas de metadados.
- O wrapper `lexer/afn_to_afd.py` agora tambem expoe `subset_dfa`, que descreve cada estado deterministico como subconjunto de estados do AFN, agrupando transicoes por conjunto de simbolos. Esse bloco facilita visualizacoes e depuracao de automatos baseados em conjuntos.
- `lexer/generator.py` grava esse dicionario em `lexer/tables.json`, que fica versionado para uso em tempo de execucao.

## 6. Execucao do lexer (`lexer/lexer.py`)

- `ScriptumLexer` carrega `tables.json` uma unica vez e constroi `LexerTables` (lista de `DFAState` + estado inicial).
- O metodo `_match_token` percorre o texto consumindo caracteres enquanto existirem transicoes. Ele memoriza o ultimo estado de aceitacao mais prioritario antes de falhar.
- Quando uma regra e aceita:
  - Construi `tokens.Token` com `span` (`text.Span`) e `metadata` (nome do padrao, indice).
  - Converte o lexema em valores nativos (inteiros, floats, strings) quando aplicavel.
- Espacos e comentarios sao ignorados conforme `LexerConfig.skip_whitespace`.
- Ao final da entrada adiciona `TokenKind.EOF` garantindo que o parser tenha um sentinela.

Com essas etapas, qualquer ajuste na especificacao (inserir um operador, mudar prioridades, criar novos tokens) pode ser propagado regenerando as tabelas, enquanto o runtime continua simples e deterministico.

# Etapa 03 — Léxico e geração do AFD

## Tokens definidos
- Literais básicos: `IDENTIFIER`, `NUMBER_LITERAL`, `STRING_LITERAL`.
- Palavras-chave latinas (`TokenKind.KEYWORD`): `mutabilis`, `constans`, `functio`, `structura`, `si`, `aliter`, `dum`, `pro`, `in`, `de`, `redde`, `frange`, `perge`, `verum`, `falsum`, `nullum`, `indefinitum`, `numerus`, `textus`, `booleanum`, `vacuum`, `quodlibet`.
- Operadores (`TokenKind.OPERATOR`): `===`, `!==`, `==`, `!=`, `??`, `?:`, `||`, `&&`, `>=`, `<=`, `>`, `<`, `**`, `+`, `-`, `*`, `/`, `%`, `!`, `=`, `.`.
- Pontuação e delimitadores: `::`, `->`, `=>`, `,`, `;`, `:`, `?`, `(`, `)`, `{`, `}`, `[`, `]`.
- Espaços e comentários ignorados: `WHITESPACE`, `COMMENT_LINE`, `COMMENT_BLOCK`.

## Alfabeto
- Letras: `A-Z`, `a-z`, sublinhado `_` (para identificadores) e símbolo `$`.
- Dígitos: `0-9` com `_` como separador interno.
- Símbolos adicionais: `{ !, ", $, %, &, ', (, ), *, +, ,, -, ., /, :, ;, <, =, >, ?, [, ], {, |, } }`, contemplando operadores, pontuação e delimitadores.

## Gerar e inspecionar o AFD
- Produza o JSON com as tabelas léxicas:
  ```bash
  python scripts/build_afd.py
  ```
- Para visualizar a saída no terminal, acrescente `--show`.
- O arquivo `src/scriptum/lexer/tables.json` guarda todas as expressões regulares, prioridades e metadados.

## Testes manuais
- Após instalar as dependências (`uv sync --extra dev`), valide a especificação:
  ```bash
  pytest -q tests/test_lexer_tokens.py
  ```
- O teste garante unicidade das palavras-chave, estrutura do JSON e presença dos literais definidos.

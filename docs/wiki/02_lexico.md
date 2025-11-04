# Léxico (DFA) e tokens (G2)

O léxico de Scriptum é implementado por um DFA manual (crate `scriptum-lexer`). A classe de linguagem continua sendo **G2** porque o léxico é regular e alimenta a gramática livre de contexto.

## Palavras-chave reservadas

| Palavra | Significado |
| --- | --- |
| `mutabilis` | declaração mutável |
| `constans` | declaração imutável |
| `functio` | definição de função / lambda |
| `structura` | literal de objeto |
| `si` | condicional |
| `aliter` | ramo `else` |
| `dum` | laço `while` |
| `pro` | laço `for-in` |
| `in` | iterador em `pro` |
| `de` | reservado para extensões futuras |
| `redde` | retorno |
| `frange` | `break` |
| `perge` | `continue` |
| `verum` / `falsum` | booleanos |
| `nullum` | valor nulo |
| `indefinitum` | valor indefinido |
| `numerus`, `textus`, `booleanum`, `vacuum`, `quodlibet` | tipos primitivos |

Qualquer identificador que coincida com esses lexemas é rejeitado pelo lexer.

## Operadores e pontuação

| Token | Prioridade | Associatividade | Descrição |
| --- | --- | --- | --- |
| `=` | 1 | direita | atribuição |
| `?:` | 2 | direita | condicional |
| `??` | 3 | esquerda | coalescência nula |
| `||` | 4 | esquerda | OR lógico |
| `&&` | 5 | esquerda | AND lógico |
| `==`, `!=`, `===`, `!==` | 6 | esquerda | igualdade |
| `>`, `>=`, `<`, `<=` | 7 | esquerda | comparação |
| `+`, `-` | 8 | esquerda | soma |
| `*`, `/`, `%` | 9 | esquerda | produto |
| `**` | 10 | **direita** | exponenciação |
| `!`, `+`, `-` (unários) | 11 | direita | unários |
| `.` | 12 | esquerda | acesso a membro |
| `[]` | 12 | esquerda | indexação |
| `()` | 12 | esquerda | chamada |

Pontuação adicional: `,`, `;`, `:`, `::`, `->`, `=>`, `?`, `{}`, `[]`, `()`.

## Literais

- **Numerus**: `42`, `3.14`, `2_500`, `1e-3`, `6.02E23`.
- **Texto**: sequência UTF-8 entre aspas duplas com escapes `\n`, `\t`, `\r`, `\"`, `\\`.
- **Booleanum**: `verum` ou `falsum`.
- **Nullum / indefinitum**: palavras-chave dedicadas.

## Comentários e espaços

- Comentário de linha: `// até o fim da linha`.
- Comentário de bloco: `/* pode aninhar */` (falha se não fechado).
- Espaços em branco (incluindo quebras de linha) são ignorados mas preservamos `Span` para diagnósticos.

## Tokens produzidos

```text
Identifier, NumeroLiteral, TextoLiteral,
Keyword(<Keyword>), Operator(<Operator>),
Delimiter(LParen|RParen|LBrace|RBrace|LBracket|RBracket),
Punctuation(Comma|Semicolon|Colon|DoubleColon|Dot|Arrow|FatArrow|Question),

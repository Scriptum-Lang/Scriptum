# Palavras-chave e comandos

Esta página resume as palavras reservadas da linguagem Scriptum. Todas elas vivem
na tupla `KEYWORDS` de `src/scriptum/tokens.py` e são reconhecidas pelo lexer
antes de qualquer outra análise. Use este guia como referência rápida enquanto
desenvolve exemplos ou atualiza o compilador.

## Declarações e tipos

| Palavra | Uso | Exemplo |
| --- | --- | --- |
| `functio` | Declara funções nomeadas ou lambdas. | `functio soma(a, b) -> numerus { redde a + b; }` |
| `mutabilis` | Declara variáveis mutáveis (equivalente a `var`). | `mutabilis numerus contador = 0;` |
| `constans` | Declara variáveis imutáveis (`const`). | `constans numerus PI = 3;` |
| `structura` | Inicia a declaração de um tipo estruturado (WIP). | `structura Ponto { numerus x; numerus y; }` |
| `numerus`, `textus`, `booleanum`, `vacuum`, `quodlibet`, `indefinitum`, `nullum` | Tipos primitivos e literais especiais. | `mutabilis textus nome = nullum;` |
| `verum`, `falsum` | Literais booleanos. | `mutabilis booleanum ativo = verum;` |

## Controle de fluxo

| Palavra | Uso | Exemplo |
| --- | --- | --- |
| `si` / `aliter` | Condicionais (`if/else`). | `si (condicao) { ... } aliter { ... }` |
| `dum` | Laço `while`. | `dum (condicao) { ... }` |
| `pro`, `in` | Laço `for ... in`. | `pro (elementum in lista) { ... }` |
| `de` | Palavras reservadas para futuros recursos (`from`/`of`). Atualmente não possuem semântica. |
| `frange` | Interrompe o laço atual (`break`). | `frange;` |
| `perge` | Continuação do laço (`continue`). | `perge;` |
| `redde` | Retorna o valor de uma função. | `redde resposta;` |

## Comandos auxiliares

Embora não sejam palavras reservadas, operadores e delimitadores também fazem
parte da “lista de comandos” de Scriptum. Todos estão definidos em
`tokens.OPERATORS`, `tokens.PUNCTUATION` e `tokens.DELIMITERS`. A tabela abaixo
mostra os principais grupos:

| Categoria | Exemplos | Observações |
| --- | --- | --- |
| Operadores aritméticos | `+ - * / % **` | O parser converte para enums (`nodes.BinaryOperator`). |
| Operadores lógicos | `&& || !` | `??` representa o coalescente nulo. |
| Comparação | `== != === !== > >= < <=` | Há variantes estritas e não estritas. |
| Atribuição e composição | `=` `?:` | `?:` é o operador condicional estilo Elvis. |
| Pontuação | `, ; : :: -> => ?` | Inclui separadores de parâmetros e arrow functions. |
| Delimitadores | `{ } ( ) [ ]` | Delimitam blocos, chamadas e arrays. |

## Funções builtin

O núcleo da biblioteca padrão vive em `src/scriptum/builtins.py` e já está
documentado em detalhes em [`docs/wiki/12_stdlib.md`](12_stdlib.md). Abaixo vai
um resumo dos símbolos mais usados:

| Função | Descrição |
| --- | --- |
| `scribe(...args: quodlibet)` | Imprime todos os argumentos com quebra de linha. |
| `longitudo(valor: textus \| [T]) -> numerus` | Tamanho de strings ou arrays. |
| `numerus/textus/booleanum(x)` | Convertem valores para os respectivos tipos. |
| `ambitus(inicio, fim, passo=1)` | Gera sequências numéricas (similar a `range`). |
| `summa`, `minimum`, `maximum`, `absolutum` | Utilidades numéricas. |
| `aliquod`, `omnia` | Ajuda em arrays booleanos (versões de `any`/`all`). |
| `enumera`, `coniunge`, `applica`, `filtra`, `ordina` | Operações comuns de coleção (`enumerate`, `zip`, `map`, `filter`, `sort`). |
| `lege(promptus="") -> textus` | Lê uma linha da entrada padrão. |

Além dessas funções globais, arrays e strings expõem métodos como `adde`,
`exime`, `extende`, `remove`, `divide`, `ad_maiusculas`, etc. Consulte
`docs/wiki/12_stdlib.md` para assinaturas, exemplos completos e códigos de erro
emitidos por cada um.

## Sugestões de uso

- Consuma esta tabela junto com `docs/wiki/03_parser.md` para entender como as
  palavras influenciam o AST.
- Em caso de mudanças no arquivo `tokens.py`, sincronize esta página e a lista
  em `docs/wiki/02_lexico.md`.
- Exemplos práticos com cada palavra aparecem na pasta `examples/` (tanto `ok`
  quanto `err`), além das seções “Builtins” e “Diagnóstico” desta wiki.

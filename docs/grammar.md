# Gramática LL(1) para expressões inteiras

Esta gramática didática cobre apenas expressões com inteiros, parênteses e os
operadores `+ - * /`. Ela serve como base para o pipeline LL(1) implementado
em Python dentro deste repositório, isolado do parser Pratt utilizado pela
linguagem Scriptum.

## Produções em EBNF

```ebnf
E  -> T E'
E' -> + T E' | - T E' | ε
T  -> F T'
T' -> * F T' | / F T' | ε
F  -> ( E ) | num
```

### Como chegamos aqui

- Partimos da gramática ambígua clássica, onde `E → E + E | E - E | T`.
  Eliminar a recursão direta à esquerda exige quebrar `E` em um núcleo (`T`)
  seguido de um sufixo (`E'`) que pode produzir cadeias com `+`/`-`.
- O mesmo raciocínio se aplica para `T`, separando multiplicação/divisão em
  `T'`. Com isso apenas `E'` e `T'` geram ε, facilitando a construção de uma
  tabela LL(1) sem conflitos porque `FIRST` e `FOLLOW` desses não-terminais
  se tornam disjuntos.
- A precedência surge naturalmente: `T` não consome `+`/`-`, então a pilha só
  retorna a `E'` depois de reduzir todos os `*`/`/`. A associatividade para
  os operadores binários fica à esquerda porque `E'` e `T'` consomem um
  operador por vez antes de voltar para si mesmos.

## Derivações guiadas

As derivações a seguir podem ser observadas diretamente na lista
`derivations` produzida pelo parser LL(1).

### `1+2*3`

1. `E ⇒ T E'`
2. `⇒ F T' E'`
3. `⇒ num T' E'` (consome `1`)
4. `⇒ ε E'` (`T' → ε`)
5. `⇒ + T E'`
6. `⇒ + F T' E'`
7. `⇒ + num T' E'` (consome `2`)
8. `⇒ + * F T' E'`
9. `⇒ + * num T' E'` (consome `3`)
10. `⇒ + * ε E' ⇒ + * ε ε`

### `(1+2)*3-4/2`

1. `E ⇒ T E' ⇒ F T' E' ⇒ ( E ) T' E'`
2. `⇒ ( T E' ) T' E' ⇒ ( F T' E' ) T' E'`
3. `⇒ ( num T' E' ) T' E'` (consome `1`)
4. `⇒ ( + T E' ) T' E'` (processa `+`)
5. `⇒ ( + num T' E' ) T' E'` (consome `2`)
6. Após `)` temos `T' → * F T'` para consumir `* 3`.
7. O `E'` final aplica `- T E'`, e dentro de `T` usamos `T' → / F T'`
   para lidar com `4 / 2`. Ambas as produções terminam com `ε`.

### `((2))`

1. `E ⇒ T E' ⇒ F T' E' ⇒ ( E ) T' E'`
2. `⇒ ( ( E ) ) T' E'`
3. `⇒ ( ( num T' E' ) ) T' E'` (consome `2`)
4. As cadeias remanescentes reduzem com `T' → ε` e `E' → ε`, respeitando
   os parênteses empilhados.

Essas derivações confirmam que a gramática é adequada para um parser LL(1)
baseado em pilha símbolo × token.

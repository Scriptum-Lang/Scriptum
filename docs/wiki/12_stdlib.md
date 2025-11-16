# Núcleo da biblioteca padrão

O compilador Scriptum agora disponibiliza um pequeno conjunto de funções builtin
que cobrem operações básicas de IO, conversões e manipulação de coleções. Todas
essas funções vivem no escopo global e respeitam o sistema de tipos da
linguagem (diagnosticando erros em tempo de análise).

## Funções globais

| Assinatura | Descrição | Exemplo |
| --- | --- | --- |
| `scribe(...args: quodlibet) -> vacuum` | Imprime todos os argumentos convertidos em texto, separados por espaço e seguidos de quebra de linha. | `scribe("salve", 42, verum);` |
| `longitudo(x: textus \| [T]) -> numerus` | Retorna o tamanho de um `textus` ou a quantidade de elementos de um array. | `mutabilis numerus n = longitudo("abc");` |
| `numerus(x) -> numerus` | Converte o valor em numerus (aceita strings numéricas, inteiros, booleanos). | `mutabilis numerus v = numerus("10");` |
| `textus(x) -> textus` | Converte o valor em string seguindo a convenção nativa (`verum`, `falsum`, `nullum`). | `mutabilis textus s = textus(42);` |
| `booleanum(x) -> booleanum` | Converte seguindo a regra estilo Python (`nullum`, `0`, strings e arrays vazios ⇒ `falsum`). | `mutabilis booleanum ativo = booleanum([]);` |
| `ambitus(inceptio, finis, passus=1) -> [numerus]` | Gera uma sequência de numerus semelhante a `range`. Aceita passos negativos e rejeita `0`. | `mutabilis valores = ambitus(0, 5);` |
| `summa(valores: [numerus]) -> numerus` | Soma todos os numerus do array (array vazio retorna `0`). | `redde summa(ambitus(0, 5));` |
| `minimum/maximum(valores: [numerus]) -> numerus` | Retorna o menor/maior elemento. Arrays vazios geram erro de execução. | `mutabilis numerus menor = minimum([4, 2, 9]);` |
| `absolutum(n: numerus) -> numerus` | Valor absoluto. | `redde absolutum(-5);` |
| `aliquod(valores: [booleanum]) -> booleanum` | Equivalente a `any`: `verum` se algum elemento for `verum`. | `aliquod([falsum, verum]);` |
| `omnia(valores: [booleanum]) -> booleanum` | Equivalente a `all`: `verum` apenas quando todos os elementos são verdadeiros e o array não é vazio. | `omnia([verum, verum]);` |
| `lege(promptus: textus = "") -> textus` | Imprime um prompt opcional e lê uma linha da entrada padrão (sem o `\n` final). | `mutabilis textus nome = lege("Nome: ");` |
| `enumera(it: [quodlibet]) -> [[numerus, quodlibet]]` | Produz pares `[indice, valor]`. | `enumera(["a", "b"]); // [[0, "a"], [1, "b"]]` |
| `coniunge(a: [quodlibet], b: [quodlibet]) -> [[quodlibet, quodlibet]]` | Zipa dois arrays até o tamanho do menor. | `coniunge([1,2], [3,4]);` |
| `applica(it: [quodlibet], f: functio(quodlibet) -> quodlibet) -> [quodlibet]` | Versão de `map`, aplicando `f` a cada elemento. | `applica([1,2], functio(x) => x * 2);` |
| `filtra(it: [quodlibet], f: functio(quodlibet) -> booleanum) -> [quodlibet]` | Versão de `filter`, retornando apenas elementos cujo predicado é `verum`. | `filtra([1,2,3], functio(x) => x % 2 == 0);` |
| `ordina(it: [quodlibet], chave: functio(quodlibet) -> quodlibet = nullum, decrescens: booleanum = falsum) -> [quodlibet]` | Ordena uma cópia do array, permitindo função de chave e modo decrescente. | `ordina([3,1,2]); // [1,2,3]` |

## Métodos de array

Usados via acesso a membro (`xs.adde(valor)`), todos com retorno `vacuum`, exceto quando indicado.

| Método | Assinatura | Comportamento |
| --- | --- | --- |
| `adde` | `adde(valor: T)` | Insere o valor ao final. |
| `exime` | `exime() -> T` | Remove e retorna o último elemento (erro em array vazio). |
| `extende` | `extende(outro: [T])` | Concatena outro array no final. |
| `inserta` | `inserta(indice: numerus, valor: T)` | Insere o valor na posição indicada (índices fora do intervalo são ajustados). |
| `remove` | `remove(valor: T)` | Elimina a primeira ocorrência, gerando erro caso não encontre. |
| `purga` | `purga()` | Esvazia o array. |

Exemplo:

```scriptum
mutabilis xs = [1, 2];
xs.adde(3);
xs.extende([4, 5]);
xs.inserta(0, 0);
xs.remove(2);
xs.purga();
```

## Métodos de textus

Chamados via `"texto".divide(",")`, todos retornando novo `textus` ou array.

| Método | Assinatura | Comportamento |
| --- | --- | --- |
| `divide` | `divide(separador: textus = " ") -> [textus]` | Divide o texto pelo separador (vazio gera erro). |
| `coniunge` | `coniunge(partes: [textus]) -> textus` | Concatena os elementos de `partes`, inserindo a string receptora entre eles. |
| `substitue` | `substitue(antigo: textus, novus: textus) -> textus` | Substitui todas as ocorrências. |
| `ad_minusculas` | `ad_minusculas() -> textus` | Converte para minúsculas. |
| `ad_maiusculas` | `ad_maiusculas() -> textus` | Converte para maiúsculas. |
| `abscinde` | `abscinde() -> textus` | Remove espaços no início e fim. |

Exemplo:

```scriptum
mutabilis partes = "a,b,c".divide(",");
mutabilis textus unido = ", ".coniunge(["a", "b", "c"]);
mutabilis textus normalizado = "  Scriptum  ".abscinde().ad_minusculas();
```

Esses recursos formam o núcleo da biblioteca padrão e podem ser estendidos em
futuras versões. Sugestões e pull requests são bem-vindos.

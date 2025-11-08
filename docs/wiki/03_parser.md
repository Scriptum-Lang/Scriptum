# Parser e estratégia de análise

O parser (crate `scriptum-parser`) adota um estilo híbrido: um *Pratt parser* para expressões e descida recursiva estruturada para declarações. A linguagem permanece **G2** porque cada produção é livre de contexto. As principais decisões de projeto são:

- **Token stream imutável** (arena `SmallVec<Token>`), evitando realocações.
- **Recuperação de erros** simples com sincronização em `;` e `}`.
- **Spans preservados** em todos os nós da AST (`scriptum-ast`).
- **ID estável** (`NodeId`) gerado pelo parser para cada nó, útil para ferramentas (LSP) e caches.

## Precedência e associatividade

A tabela de precedência em [02_lexico.md](02_lexico.md) é implementada diretamente nas funções `parse_*`. `**` é associativo à direita; os demais operadores binários são à esquerda. `?:` é tratado após `??`, com `=` aplicando associação à direita.

## Resolução do *dangling else*

A regra `IfInstrucao` sempre consome o `aliter` mais próximo, graças ao uso de `parse_embedded_statement`. Não há ambiguidade na AST: o bloco de `aliter` é armazenado explicitamente.

## Generics e lambdas

`functio` suporta lista opcional de genéricos (`functio max<T>(...)`) tanto em funções quanto em lambdas. O parser aceita generics sintaticamente; a validação semântica fica a cargo da crate `scriptum-types`.

## Estrutura de erro

`ParseOutput` contém:

```rust
pub struct ParseOutput {
    pub module: Module,
    pub diagnostics: Vec<ParseError>,
}
```

`ParseError` inclui mensagem amigável e `Span`. Em modo `--json`, o CLI serializa esse objeto via `serde`.

## Normalização da AST

- `StringInterner` mantém símbolos únicos, evitando comparações custosas.
- `ExpressionKind::Assignment` cobre atribuições encadeadas (`a = b = c`).
- `StatementKind::Block` permite blocos inline (ex.: `si cond { ... } aliter { ... }`).

### Produções especiais

- **Objetos**: `structura { campo: expr, ... }`.
- **Arrays**: `[expr, expr, ...]`.
- **Lambdas**: `functio (params) => expr` ou `functio (params) { ... }`.

## Integração com outras fases

O parser retorna `Module` com todos os `NodeId` e `Span`. As fases seguintes consomem essa AST:

1. `scriptum-types` – checagem semântica/contextual.
2. `scriptum-ir::lower_module` – conversão para IR.
3. `scriptum-codegen::generate` – pretty-printer/bytecode.

Quando o parser acumula erros, as fases subsequentes podem optar por abortar ou prosseguir em modo tolerante (o CLI aborta na etapa atual).

## Modo instrumentado e ponte com LL(1)

O `ScriptumParser` expõe agora o tipo `ParserTrace`. Ao instanciá-lo (`trace = ParserTrace()`) e passá-lo para `parser.parse(source, trace=trace)`, cada chamada externa de `_parse_expression` gera:

- Uma **árvore leve** (`ParserTraceNode`) com `span`, `node_id`, lexemas relevantes e filhos imediatos. Isso permite depurar rapidamente com `trace.expression_trees[-1].pretty()`.
- Um **log textual** (`trace.productions`) indicando as etapas executadas pelo Pratt parser (chamadas, indexações, operadores) e, quando aplicável, as mesmas derivações que o pipeline LL(1) produz.

Sempre que uma expressão é puramente aritmética (`num`, `+ - * /` e parênteses), o parser delega a análise para `LL1Parser`, reconstrói a AST a partir da árvore LL(1) e insere as derivações completas (terminando em `ACCEPT`) no `ParserTrace`. O comando `python -m scriptum.devtools.ll1_crosscheck` utiliza essas estruturas para comparar automaticamente a árvore do Pratt com a árvore LL(1), exibindo ambos os lados e o log quando encontra divergências.

## Apêndice: pipeline LL(1) didático

Para fins educacionais, mantemos em `src/ll1calc/` um conjunto de ferramentas LL(1) enxuto, dedicado apenas a expressões com `+ - * / ( )` e inteiros:

1. A gramática fatorada e sem recursão à esquerda está descrita em `docs/grammar.md`.
2. `first_follow.py` calcula automaticamente os conjuntos FIRST/FOLLOW, reaproveitados por `ll1_table.py` para gerar a tabela LL(1).
3. `parser.py` implementa o algoritmo preditivo com pilha, registrando cada produção aplicada e montando uma árvore sintática completa.
4. `tests/test_parser.py` valida os exemplos mínimos exigidos em sala (`42`, `1+2*3`, `(1+2)*3-4/2`, `((2))`) e cobre erros léxicos/sintáticos.

Esse pipeline não substitui o Pratt parser; ele existe como material de apoio para disciplinas de compiladores e para comparar abordagens (LL(1) vs. descida recursiva/Pratt).

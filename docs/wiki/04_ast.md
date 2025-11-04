# AST canônica (`scriptum-ast`)

A crate `scriptum-ast` define uma representação imutável para a sintaxe de Scriptum. Os objetivos principais são:

- **IDs estáveis** (`NodeId`) para todos os nós (módulos, itens, declarações, expressões e tipos).
- **Spans precisos** (`scriptum_utils::Span` em bytes UTF-8) para diagnósticos e formatação.
- **Interner compartilhado** (`StringInterner`) para garantir que `Symbol` seja uma chave numérica compacta.

## Estrutura principal

```rust
pub struct Module {
    pub id: NodeId,
    pub span: Span,
    pub interner: StringInterner,
    pub items: Vec<Item>,
}

pub enum ItemKind {
    Function(Function),
    Let(VarDecl),
}
```

Funções (`Function`) carregam parâmetros, tipo de retorno opcional e `Block`. Declarações (`StatementKind`) incluem variantes para `let`, `const`, `if`, `while`, `for`, `break`, `continue`, `return`, blocos e instruções de expressão.

### Expressões

`ExpressionKind` contempla:

- Literais (`Literal`): numerus, textus, booleanum, nullum, indefinitum.
- `Identifier(Symbol)` usando o interner global.
- `Unary`, `Binary`, `Logical`, `NullishCoalesce`, `Conditional`, `Assignment`.
- Pós-fixos: `Call`, `Index`, `Member`.
- Estruturas: `ArrayLiteral`, `ObjectLiteral`, `Lambda`.

Cada `Expression` possui `NodeId`, `Span` e `ExpressionKind`.

### Tipos

`TypeExprKind` representa anotações sintáticas: simples (`Symbol`), arrays, objetos `{ campo: Tipo }`, funções (`functio(...) -> ...`), opcionais (`Tipo?`) e tuplas (desdobradas internamente em objetos indexados).

## Visitor e extensibilidade

A trait `Visitor` percorre a AST de maneira previsível, possibilitando implementações customizadas (por exemplo, caminhadas semânticas, formatação ou análises estáticas). Cada método possui implementação padrão que garante travessia completa.

## Convenções

- Novos campos devem preservar `Span` e `NodeId`.
- Use o interner (`StringInterner::intern`) para criar `Symbol` dentro do parser; nunca armazene strings crus.
- Estruturas são `serde::Serialize`/`Deserialize`, permitindo dumps em JSON (com suporte no CLI).

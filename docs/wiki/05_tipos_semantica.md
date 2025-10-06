# Tipos e análise semântica (G1)

A verificação de tipos (`scriptum-types`) é **sensível ao contexto** (classe **G1**). Ela depende do histórico de declarações e escopos, fornecendo diagnósticos ricos.

## Domínio de tipos

Enumeração `Type`:

- `Numerus`, `Textus`, `Booleanum`, `Vacuum`, `Nullum`, `Indefinitum`, `Quodlibet`.
- `Array(Box<Type>)`.
- `Object(IndexMap<Symbol, Type>)`.
- `Function { params: Vec<Type>, ret: Box<Type> }`.
- `Optional(Box<Type>)`.

Tipos opcionais aceitam `nullum` e participam de `??`.

## Regras principais

1. **Declaração antes do uso**: `SymbolTable` mantém pilha de escopos; referências não declaradas geram `S100`.
2. **Atribuição**: `is_assignable` verifica compatibilidade e aceita `quodlibet` como supertipo.
3. **Retorno**: `T010` é emitido se o tipo retornado não corresponde ao declarado.
4. **Condicionais/loops**: condições devem ser `booleanum` (`T020`, `T021`).
5. **Iteração**: `pro x in expr` requer `expr` iterável (`array` ou `quodlibet`), senão `T030`.
6. **Chamadas**: funções verificam aridade e tipos (`T300`, `T301`).

## Diagnósticos

Cada diagnóstico possui código `Txxx` (tipos) ou `Sxxx` (símbolos). Estrutura:

```rust
pub struct TypeDiagnostic {
    pub code: &'static str,
    pub message: String,
    pub span: Span,
    pub notes: Vec<String>,
}
```

`TypeCheckOutput` agrega a lista de diagnósticos e é serializável (`serde`).

## Fluxo

1. O parser entrega `Module` + `StringInterner`.
2. A primeira passada registra assinaturas de funções.
3. Declarações/expressões são percorridas com a `SymbolTable` aninhada.
4. Erros não interrompem a visita; múltiplos diagnósticos são reportados.

## Extensões futuras

- Inferência de tipos para genéricos (`functio<T>`).
- Tipos `enum` e `struct` nomeados.
- Sistema de efeitos (`vacuum` vs `!vacuum`), integrado ao IR.

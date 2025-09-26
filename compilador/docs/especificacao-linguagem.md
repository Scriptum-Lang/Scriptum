# Especificação da Linguagem Scriptum (.stm)

A linguagem Scriptum é imperativa com tipagem estática leve e sintaxe inspirada
em linguagens latinas.

## Léxico

* Identificadores: `[A-Za-z_][A-Za-z0-9_]*`
* Palavras-chave: `def`, `finis`, `si`, `alioqui`, `dum`, `verum`, `falsum`, `reditus`.
* Operadores: `+`, `-`, `*`, `/`, `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`.
* Comentários: `// até o fim da linha` ou `/* bloco */`.

## Sintaxe (BNF simplificada)

```
<module>       ::= { <function> }
<function>     ::= "def" <ident> "(" [ <param-list> ] ")" <block>
<param-list>   ::= <ident> { "," <ident> }
<block>        ::= "{" { <statement> } "}"
<statement>    ::= <let> | <assignment> | <if> | <while> | <return> | <expr> ";"
<let>          ::= "def" <ident> "=" <expr> ";"
<assignment>   ::= <ident> "=" <expr> ";"
<if>           ::= "si" <expr> <block> [ "alioqui" <block> ]
<while>        ::= "dum" <expr> <block>
<return>       ::= "reditus" <expr> ";"
<expr>         ::= <term> { ("+" | "-") <term> }
<term>         ::= <factor> { ("*" | "/") <factor> }
<factor>       ::= <number> | <ident> | "(" <expr> ")"
```

## Tipos

* `numerus` (ponto flutuante 64-bit)
* `verum` / `falsum` (booleano)

Coerções implícitas não são realizadas; todas as conversões devem ser explícitas.

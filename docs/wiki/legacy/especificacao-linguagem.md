# EspecificaÃ§Ã£o da Linguagem Scriptum (.stm)

A linguagem Scriptum Ã© imperativa com tipagem estÃ¡tica leve e sintaxe inspirada
em linguagens latinas.

## LÃ©xico

* Identificadores: `[A-Za-z_][A-Za-z0-9_]*`
* Palavras-chave: `definire`, `finis`, `si`, `alioqui`, `dum`, `verum`, `falsum`, `reditus`.
* Operadores: `+`, `-`, `*`, `/`, `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`.
* ComentÃ¡rios: `// atÃ© o fim da linha` ou `/* bloco */`.

## Sintaxe (BNF simplificada)

```
<module>       ::= { <function> }
<function>     ::= "definire" <ident> "(" [ <param-list> ] ")" <block>
<param-list>   ::= <ident> { "," <ident> }
<block>        ::= "{" { <statement> } "}"
<statement>    ::= <let> | <assignment> | <if> | <while> | <return> | <expr> ";"
<let>          ::= "definire" <ident> "=" <expr> ";"
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

CoerÃ§Ãµes implÃ­citas nÃ£o sÃ£o realizadas; todas as conversÃµes devem ser explÃ­citas.

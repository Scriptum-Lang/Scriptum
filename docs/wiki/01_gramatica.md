# Gramática de Scriptum (G2)

A gramática da linguagem Scriptum é livre de contexto (classe **G2** na hierarquia de Chomsky). Ela é definida em EBNF com complementos em BNF para trechos específicos. Cada produção assume um arquivo UTF-8 único.

```ebnf
Modulo        = { Item } ;
Item          = Funcao | VariavelGlobal ;

Funcao        = "functio" Identificador [Genericos] "(" [ListaParametros] ")" ["->" Tipo] Bloco ;
Genericos     = "<" ListaIdent ">" ;
ListaParametros = Parametro { "," Parametro } ;
Parametro     = Identificador [":" Tipo] ;

VariavelGlobal = ("mutabilis" | "constans") Identificador [":" Tipo] ["=" Expressao] ";" ;

Bloco         = "{" { Declaracao } "}" ;
Declaracao    = VariavelLocal | Instrucao ;
VariavelLocal = ("mutabilis" | "constans") Identificador [":" Tipo] ["=" Expressao] ";" ;

Instrucao     = ExprInstrucao
              | Retorno
              | IfInstrucao
              | WhileInstrucao
              | ForInstrucao
              | Bloco
              | "frange" ";"
              | "perge" ";" ;
ExprInstrucao = Expressao ";" ;
Retorno       = "redde" [Expressao] ";" ;
IfInstrucao   = "si" Expressao Instrucao ["aliter" Instrucao] ;
WhileInstrucao= "dum" Expressao Instrucao ;
ForInstrucao  = "pro" Identificador "in" Expressao Instrucao ;

Expressao     = Atribuicao ;
Atribuicao    = Ternario ["=" Atribuicao] ;
Ternario      = Coalescencia [ "?" Expressao ":" Expressao ] ;
Coalescencia  = LogicoOu { "??" LogicoOu } ;
LogicoOu      = LogicoE { "||" LogicoE } ;
LogicoE       = Igualdade { "&&" Igualdade } ;
Igualdade     = Comparacao { ("==" | "!=" | "===" | "!==") Comparacao } ;
Comparacao    = Soma { (">" | ">=" | "<" | "<=") Soma } ;
Soma          = Produto { ("+" | "-") Produto } ;
Produto       = Potencia { ("*" | "/" | "%") Potencia } ;
Potencia      = Unario ["**" Potencia] ; (* associação à direita *)
Unario        = ("+" | "-" | "!") Unario | Posfixo ;
Posfixo       = Primario { PosfixoSufixo } ;
PosfixoSufixo = Chamado | Indexacao | Acesso ;
Chamado       = "(" [ListaArgumentos] ")" ;
Indexacao     = "[" Expressao "]" ;
Acesso        = "." Identificador ;

Primario      = Literal
              | Identificador
              | "(" Expressao ")"
              | "[" [ListaArgumentos] "]"
              | Objeto
              | Lambda ;

ListaArgumentos = Expressao { "," Expressao } ;
Objeto        = "structura" "{" [CampoObjeto { "," CampoObjeto }] "}" ;
CampoObjeto   = Identificador ":" Expressao ;
Lambda        = "functio" [Genericos] "(" [ListaParametros] ")" ["->" Tipo] ("=>" Expressao | Bloco) ;

Literal       = Numero | Texto | Booleano | "nullum" | "indefinitum" ;
Numero        = ["-"] Digitos ["." Digitos] [Expoente] ;
Texto         = '"' { Caractere | Escape } '"' ;
Booleano      = "verum" | "falsum" ;

Tipo          = TipoSimples ["?" | SufixoTipo] ;
TipoSimples   = Identificador
              | "[" Tipo "]"
              | "{" [CampoTipo { "," CampoTipo }] "}"
              | "functio" "(" [ListaTipos] ")" "->" Tipo ;
CampoTipo     = Identificador ":" Tipo ;
ListaTipos    = Tipo { "," Tipo } ;
SufixoTipo    = "[" "]" ;

Identificador = Letra { Letra | Digito | '_' | '$' } ;
Digitos       = Digito { Digito | '_' } ;
Expoente      = ("e" | "E") ["+" | "-"] Digitos ;
```

### Observações

- `aliter` resolve o *dangling else* associando-se sempre ao `si` mais interno.
- `Potencia` é o único operador binário com associação à direita.
- Tipos opcionais são anotados com `?` (por exemplo `numerus?`) e se integram à checagem de nullidade.
- `Lambda` aceita corpo como expressão (`=>`) ou bloco completo.

### BNF complementar

A produção de `Léxico` (detalhada em [02_lexico.md](02_lexico.md)) garante que `Identificador` nunca colida com palavras-chave reservadas.

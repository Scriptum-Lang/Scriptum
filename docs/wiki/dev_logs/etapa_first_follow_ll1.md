# FIRST/FOLLOW da gramática Scriptum

## Gramática (BNF)
```bnf
Modulo -> Item Modulo | ε
Item -> Funcao | VariavelGlobal
Funcao -> functio Identificador FuncaoGenericosOpt ( ParametrosOpt ) FuncaoTipoRetOpt Bloco
FuncaoGenericosOpt -> Genericos | ε
ParametrosOpt -> ListaParametros | ε
FuncaoTipoRetOpt -> -> Tipo | ε
Genericos -> < ListaIdent >
ListaIdent -> Identificador ListaIdentTail
ListaIdentTail -> , Identificador ListaIdentTail | ε
ListaParametros -> Parametro ListaParametrosTail
ListaParametrosTail -> , Parametro ListaParametrosTail | ε
Parametro -> Identificador ParametroTipoOpt
ParametroTipoOpt -> : Tipo | ε
VariavelGlobal -> VarGlobalPrefix Identificador VarGlobalTipoOpt VarGlobalInitOpt ;
VarGlobalPrefix -> mutabilis | constans
VarGlobalTipoOpt -> : Tipo | ε
VarGlobalInitOpt -> = Expressao | ε
Bloco -> { BlocoConteudoOpt }
BlocoConteudoOpt -> Declaracao BlocoConteudoOpt | ε
Declaracao -> VariavelLocal | Instrucao
VariavelLocal -> VarLocalPrefix Identificador VarLocalTipoOpt VarLocalInitOpt ;
VarLocalPrefix -> mutabilis | constans
VarLocalTipoOpt -> : Tipo | ε
VarLocalInitOpt -> = Expressao | ε
Instrucao -> ExprInstrucao | Retorno | IfInstrucao | WhileInstrucao | ForInstrucao | Bloco | frange ; | perge ;
ExprInstrucao -> Expressao ;
Retorno -> redde RetornoExprOpt ;
RetornoExprOpt -> Expressao | ε
IfInstrucao -> si Expressao Instrucao IfElseOpt
IfElseOpt -> aliter Instrucao | ε
WhileInstrucao -> dum Expressao Instrucao
ForInstrucao -> pro Identificador in Expressao Instrucao
Expressao -> Atribuicao
Atribuicao -> Ternario AtribuicaoOpt
AtribuicaoOpt -> = Atribuicao | ε
Ternario -> Coalescencia TernarioOpt
TernarioOpt -> ? Expressao : Expressao | ε
Coalescencia -> LogicoOu CoalescenciaTail
CoalescenciaTail -> ?? LogicoOu CoalescenciaTail | ε
LogicoOu -> LogicoE LogicoOuTail
LogicoOuTail -> || LogicoE LogicoOuTail | ε
LogicoE -> Igualdade LogicoETail
LogicoETail -> && Igualdade LogicoETail | ε
Igualdade -> Comparacao IgualdadeTail
IgualdadeTail -> IgualdadeOp Comparacao IgualdadeTail | ε
IgualdadeOp -> == | != | === | !==
Comparacao -> Soma ComparacaoTail
ComparacaoTail -> CompOp Soma ComparacaoTail | ε
CompOp -> > | >= | < | <=
Soma -> Produto SomaTail
SomaTail -> SomaOp Produto SomaTail | ε
SomaOp -> + | -
Produto -> Potencia ProdutoTail
ProdutoTail -> ProdOp Potencia ProdutoTail | ε
ProdOp -> * | / | %
Potencia -> Unario PotenciaOpt
PotenciaOpt -> ** Potencia | ε
Unario -> UnarioOp Unario | Posfixo
UnarioOp -> + | - | !
Posfixo -> Primario PosfixoTail
PosfixoTail -> PosfixoSufixo PosfixoTail | ε
PosfixoSufixo -> Chamado | Indexacao | Acesso
Chamado -> ( ArgumentosOpt )
ArgumentosOpt -> ListaArgumentos | ε
Indexacao -> [ Expressao ]
Acesso -> . Identificador
Primario -> Literal | Identificador | ( Expressao ) | [ ArgumentosOpt ] | Objeto | Lambda
ListaArgumentos -> Expressao ListaArgumentosTail
ListaArgumentosTail -> , Expressao ListaArgumentosTail | ε
Objeto -> structura { ObjetoCamposOpt }
ObjetoCamposOpt -> CampoObjeto ObjetoCamposTail | ε
ObjetoCamposTail -> , CampoObjeto ObjetoCamposTail | ε
CampoObjeto -> Identificador : Expressao
Lambda -> functio LambdaGenericosOpt ( ParametrosOpt ) LambdaRetOpt LambdaCorpo
LambdaGenericosOpt -> Genericos | ε
LambdaRetOpt -> -> Tipo | ε
LambdaCorpo -> => Expressao | Bloco
Literal -> Numero | Texto | Booleano | nullum | indefinitum
Booleano -> verum | falsum
Tipo -> TipoSimples TipoPosOpt
TipoPosOpt -> ? | SufixoTipo | ε
TipoSimples -> Identificador | [ Tipo ] | { TipoCamposOpt } | functio ( ListaTiposOpt ) -> Tipo
TipoCamposOpt -> CampoTipo TipoCamposTail | ε
TipoCamposTail -> , CampoTipo TipoCamposTail | ε
CampoTipo -> Identificador : Tipo
ListaTiposOpt -> ListaTipos | ε
ListaTipos -> Tipo ListaTiposTail
ListaTiposTail -> , Tipo ListaTiposTail | ε
SufixoTipo -> [ ]
```

## Conjuntos FIRST e FOLLOW
| Não-terminal | FIRST | FOLLOW |
| --- | --- | --- |
| `Modulo` | ε, constans, functio, mutabilis | $ |
| `Item` | constans, functio, mutabilis | $, constans, functio, mutabilis |
| `Funcao` | functio | $, constans, functio, mutabilis |
| `FuncaoGenericosOpt` | ε, < | ( |
| `ParametrosOpt` | ε, Identificador | ) |
| `FuncaoTipoRetOpt` | ε, -> | { |
| `Genericos` | < | ( |
| `ListaIdent` | Identificador | > |
| `ListaIdentTail` | ε, , | > |
| `ListaParametros` | Identificador | ) |
| `ListaParametrosTail` | ε, , | ) |
| `Parametro` | Identificador | ), , |
| `ParametroTipoOpt` | ε, : | ), , |
| `VariavelGlobal` | constans, mutabilis | $, constans, functio, mutabilis |
| `VarGlobalPrefix` | constans, mutabilis | Identificador |
| `VarGlobalTipoOpt` | ε, : | ;, = |
| `VarGlobalInitOpt` | ε, = | ; |
| `Bloco` | { | !, !=, !==, $, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `BlocoConteudoOpt` | ε, !, (, +, -, Identificador, Numero, Texto, [, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, { | } |
| `Declaracao` | !, (, +, -, Identificador, Numero, Texto, [, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, { | !, (, +, -, Identificador, Numero, Texto, [, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `VariavelLocal` | constans, mutabilis | !, (, +, -, Identificador, Numero, Texto, [, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `VarLocalPrefix` | constans, mutabilis | Identificador |
| `VarLocalTipoOpt` | ε, : | ;, = |
| `VarLocalInitOpt` | ε, = | ; |
| `Instrucao` | !, (, +, -, Identificador, Numero, Texto, [, dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, { | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `ExprInstrucao` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `Retorno` | redde | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `RetornoExprOpt` | ε, !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | ; |
| `IfInstrucao` | si | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `IfElseOpt` | ε, aliter | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `WhileInstrucao` | dum | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `ForInstrucao` | pro | !, (, +, -, Identificador, Numero, Texto, [, aliter, constans, dum, falsum, frange, functio, indefinitum, mutabilis, nullum, perge, pro, redde, si, structura, verum, {, } |
| `Expressao` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Atribuicao` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `AtribuicaoOpt` | ε, = | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Ternario` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `TernarioOpt` | ε, ? | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Coalescencia` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `CoalescenciaTail` | ε, ?? | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `LogicoOu` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `LogicoOuTail` | ε, || | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `LogicoE` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `LogicoETail` | ε, && | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Igualdade` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `IgualdadeTail` | ε, !=, !==, ==, === | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `IgualdadeOp` | !=, !==, ==, === | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum |
| `Comparacao` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ComparacaoTail` | ε, <, <=, >, >= | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `CompOp` | <, <=, >, >= | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum |
| `Soma` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `SomaTail` | ε, +, - | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `SomaOp` | +, - | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum |
| `Produto` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ProdutoTail` | ε, %, *, / | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ProdOp` | %, *, / | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum |
| `Potencia` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `PotenciaOpt` | ε, ** | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Unario` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `UnarioOp` | !, +, - | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum |
| `Posfixo` | (, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `PosfixoTail` | ε, (, ., [ | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `PosfixoSufixo` | (, ., [ | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Chamado` | ( | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ArgumentosOpt` | ε, !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | ), ] |
| `Indexacao` | [ | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Acesso` | . | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Primario` | (, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ListaArgumentos` | !, (, +, -, Identificador, Numero, Texto, [, falsum, functio, indefinitum, nullum, structura, verum | ), ] |
| `ListaArgumentosTail` | ε, , | ), ] |
| `Objeto` | structura | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `ObjetoCamposOpt` | ε, Identificador | } |
| `ObjetoCamposTail` | ε, , | } |
| `CampoObjeto` | Identificador | ,, } |
| `Lambda` | functio | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `LambdaGenericosOpt` | ε, < | ( |
| `LambdaRetOpt` | ε, -> | =>, { |
| `LambdaCorpo` | =>, { | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Literal` | Numero, Texto, falsum, indefinitum, nullum, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Booleano` | falsum, verum | !, !=, !==, %, &&, (, ), *, **, +, ,, -, ., /, :, ;, <, <=, =, ==, ===, >, >=, ?, ??, Identificador, Numero, Texto, [, ], dum, falsum, frange, functio, indefinitum, nullum, perge, pro, redde, si, structura, verum, {, ||, } |
| `Tipo` | Identificador, [, functio, { | ), ,, ;, =, =>, ?, [, ], {, } |
| `TipoPosOpt` | ε, ?, [ | ), ,, ;, =, =>, ?, [, ], {, } |
| `TipoSimples` | Identificador, [, functio, { | ), ,, ;, =, =>, ?, [, ], {, } |
| `TipoCamposOpt` | ε, Identificador | } |
| `TipoCamposTail` | ε, , | } |
| `CampoTipo` | Identificador | ,, } |
| `ListaTiposOpt` | ε, Identificador, [, functio, { | ) |
| `ListaTipos` | Identificador, [, functio, { | ) |
| `ListaTiposTail` | ε, , | ) |
| `SufixoTipo` | [ | ), ,, ;, =, =>, ?, [, ], {, } |

## A gramática é LL(1)?

A construção da tabela LL(1) apresenta conflitos porque algumas produções que geram ε compartilham lookaheads com alternativas não vazias:

- `AtribuicaoOpt`: lookahead(s) =
- `CoalescenciaTail`: lookahead(s) ??
- `ComparacaoTail`: lookahead(s) <, <=, >, >=
- `IfElseOpt`: lookahead(s) aliter
- `IgualdadeTail`: lookahead(s) !=, !==, ==, ===
- `LogicoETail`: lookahead(s) &&
- `LogicoOuTail`: lookahead(s) ||
- `PosfixoTail`: lookahead(s) (, ., [
- `PotenciaOpt`: lookahead(s) **
- `ProdutoTail`: lookahead(s) %, *, /
- `SomaTail`: lookahead(s) +, -
- `TernarioOpt`: lookahead(s) ?
- `TipoPosOpt`: lookahead(s) ?, [

Os conflitos concentram-se nos não-terminais em forma de sufixo (`*Tail`, `*Opt`), responsáveis por operadores encadeados. O mesmo token que inicia a produção recursiva também pertence ao FOLLOW do não-terminal, gerando colisões ao preencher a tabela LL(1).
Conclusão: a gramática **não** é LL(1) e exige um parser com mais lookahead ou uma abordagem diferente (por exemplo, Pratt parser) para tratar as expressões com precedência.

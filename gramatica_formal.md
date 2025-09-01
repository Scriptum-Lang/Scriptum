# Projeto Integrador: Gramática Formal da Linguagem **Scriptum** 📝

 > Primeira versão **G2 (Livre de Contexto)** e trilha de evolução para **G1 (Sensível ao Contexto)**, exemplos de derivações e análise de ambiguidades.

---

## 🎯 **Desenvolvimento da Gramática para o Compilador Scriptum**

A linguagem **Scriptum** tem como princípios:  
- **Sintaxe JS‑like** (expressões, blocos, encadeamentos), mas com **terminais em latim**;  
- **Tipagem explícita** com anotações `: Tipo` (estilo TypeScript);  
- **Controle de fluxo** com `si/aliter`, `dum`, `pro` (com variantes `in/de`);  
- **Evolução planejada**: iniciar em **G2** para parsing, e evoluir para **G1** para checagem de tipos (contexto).

---

## 📋 **Gramática Formal Desenvolvida**

### **Definição Completa G = (V, T, P, S)**

**Símbolo inicial (S)**: `Programa`

**Conjunto de Variáveis (V)** (não-terminais, em português):
```
V = {
  Programa, Elemento, Bloco, Instrucao, InstrucaoBloco,
  InstrucaoIf, InstrucaoWhile, InstrucaoFor, CabecaFor,
  Declaracao, DeclaracaoVar, AnotacaoTipo, InicializacaoOpt,
  DeclaracaoFuncao, ParametrosFunc, ListaParametros, Parametro, TipoRetornoOpt,
  Expressao, ExpressaoAtrib, OperadorAtrib, ExpressaoCond,
  ExpressaoLogOu, ExpressaoLogE, ExpressaoCoalesc,
  ExpressaoIgual, ExpressaoRel, ExpressaoAdd, ExpressaoMul, ExpressaoExp,
  ExpressaoUnaria, ExpressaoPostfix, Sufixos, Chamada, ListaArgs,
  AcessoPonto, AcessoIndexado, OpcionalChain,
  Primario, Tipo, TipoPrim, TipoArray, TipoObjeto, CamposTipo, CampoTipo, TipoFuncao,
  Literal, EstruturaObjeto, ParesObj, ParObj, EstruturaArray, ItensArr,
  DestructAnotado, DestructPadrao, ObjectPattern, ArrayPattern, ListaPatObj, PatObj, ListaPatArr, PatArr
}
```

**Conjunto de Terminais (T)** (palavras-chave e símbolos em **latim**; literais são tokens léxicos):
```
T = {
  // Declaração/Tipos
  mutabilis, constans, functio, classis, structor, novum, hoc, super,
  // Controle
  si, aliter, dum, pro, in, de, redde, frange, perge,
  // Literais
  verum, falsum, nullum, indefinitum,
  // Tipos primitivos e especiais
  numerus, textus, booleanum, vacuum, quodlibet,
  // Operadores e pontuação
  "+", "-", "*", "/", "%", "**",
  "=", "+=", "-=", "*=", "/=", "%=",
  "==", "!=", "===", "!==",
  "<", "<=", ">", ">=",
  "&&", "||", "!", "??", "?.",
  ",", ";", ".", ":", "?", "(", ")", "[", "]", "{", "}",
  // Tokens léxicos
  Ident, NumeroLiteral, TextoLiteral
}
```

**Produções (P)** — forma principal (EBNF). Para efeito de formalização, versões **BNF** equivalentes podem ser derivadas removendo `?/*/+` por fatoração:

```ebnf
Programa           -> Elemento* EOF ;

Elemento           -> Declaracao
                    | DeclaracaoFuncao
                    | Instrucao ;

Bloco              -> "{" Elemento* "}" ;

Declaracao         -> DeclaracaoVar ";" ;

DeclaracaoVar      -> ("mutabilis" | "constans") Ident AnotacaoTipo? InicializacaoOpt
                    | ("mutabilis" | "constans") DestructAnotado InicializacaoOpt ;

AnotacaoTipo       -> ":" Tipo ;
InicializacaoOpt   -> ("=" Expressao)? ;

DestructAnotado    -> DestructPadrao AnotacaoTipo? ;
DestructPadrao     -> ObjectPattern | ArrayPattern ;

ObjectPattern      -> "{" ListaPatObj? "}" ;
ListaPatObj        -> PatObj ("," PatObj)* ;
PatObj             -> Ident (":" Ident)? ;

ArrayPattern       -> "[" ListaPatArr? "]" ;
ListaPatArr        -> PatArr ("," PatArr)* ;
PatArr             -> Ident ;

DeclaracaoFuncao   -> "functio" Ident ParametrosFunc TipoRetornoOpt Bloco ;
TipoRetornoOpt     -> AnotacaoTipo? ;

ParametrosFunc     -> "(" ListaParametros? ")" ;
ListaParametros    -> Parametro ("," Parametro)* ;
Parametro          -> (Ident | DestructPadrao) AnotacaoTipo? ("=" Expressao)? ;

Instrucao          -> InstrucaoBloco
                    | InstrucaoIf
                    | InstrucaoWhile
                    | InstrucaoFor
                    | InstrucaoReturn
                    | "frange" ";"
                    | "perge" ";"
                    | Expressao ";" ;

InstrucaoBloco     -> Bloco ;

InstrucaoIf        -> "si" "(" Expressao ")" Instrucao ("aliter" Instrucao)? ;
InstrucaoWhile     -> "dum" "(" Expressao ")" Instrucao ;

InstrucaoFor       -> "pro" "(" CabecaFor ")" Instrucao ;
CabecaFor          -> ForClassico | ForIn | ForOf ;
ForClassico        -> ForInitOpt ";" ExpressaoOpt ";" ExpressaoOpt ;
ForIn              -> (DeclaracaoVar | Expressao) "in" Expressao ;
ForOf              -> (DeclaracaoVar | Expressao) "de" Expressao ;
ForInitOpt         -> (DeclaracaoVar | Expressao)? ;
ExpressaoOpt       -> Expressao? ;

InstrucaoReturn    -> "redde" ExpressaoOpt ";" ;

Tipo               -> TipoPrim
                    | TipoArray
                    | TipoObjeto
                    | TipoFuncao
                    | Ident ;

TipoPrim           -> "numerus" | "textus" | "booleanum" | "vacuum"
                    | "nullum" | "indefinitum" | "quodlibet" ;

TipoArray          -> Tipo "[]" ;

TipoObjeto         -> "{" CamposTipo? "}" ;
CamposTipo         -> CampoTipo ("," CampoTipo)* ;
CampoTipo          -> Ident ":" Tipo ;

TipoFuncao         -> "functio" "<" ParamTipos? ">"? "(" TiposParametros? ")" "->" Tipo ;
ParamTipos         -> Ident ("," Ident)* ;
TiposParametros    -> Tipo ("," Tipo)* ;

Expressao          -> ExpressaoAtrib ;

ExpressaoAtrib     -> ExpressaoCond (OperadorAtrib ExpressaoAtrib)? ;
OperadorAtrib      -> "=" | "+=" | "-=" | "*=" | "/=" | "%=" ;

ExpressaoCond      -> ExpressaoLogOu ("?" Expressao ":" Expressao)? ;

ExpressaoLogOu     -> ExpressaoLogE ( "||" ExpressaoLogE )* ;
ExpressaoLogE      -> ExpressaoCoalesc ( "&&" ExpressaoCoalesc )* ;
ExpressaoCoalesc   -> ExpressaoIgual ( "??" ExpressaoIgual )* ;

ExpressaoIgual     -> ExpressaoRel ( ("==" | "!=" | "===" | "!==") ExpressaoRel )* ;
ExpressaoRel       -> ExpressaoAdd ( ("<" | "<=" | ">" | ">=") ExpressaoAdd )* ;
ExpressaoAdd       -> ExpressaoMul ( ("+" | "-") ExpressaoMul )* ;
ExpressaoMul       -> ExpressaoExp ( ("*" | "/") ExpressaoExp )* ;
ExpressaoExp       -> ExpressaoUnaria ( "**" ExpressaoUnaria )* ;

ExpressaoUnaria    -> ("+" | "-" | "!" ) ExpressaoUnaria
                    | ExpressaoPostfix ;

ExpressaoPostfix   -> Primario Sufixos* ;
Sufixos            -> Chamada | AcessoPonto | AcessoIndexado | OpcionalChain ;
Chamada            -> "(" ListaArgs? ")" ;
ListaArgs          -> Expressao ("," Expressao)* ;
AcessoPonto        -> "." Ident ;
AcessoIndexado     -> "[" Expressao "]" ;
OpcionalChain      -> "?." (Chamada | AcessoPonto | AcessoIndexado) ;

Primario           -> "(" Expressao ")"
                    | "novum" ExpressaoPostfix
                    | "hoc"
                    | "super" Chamada?
                    | Literal
                    | EstruturaObjeto
                    | EstruturaArray
                    | Ident ;

Literal            -> NumeroLiteral
                    | TextoLiteral
                    | "verum" | "falsum"
                    | "nullum" | "indefinitum" ;

EstruturaObjeto    -> "{" ParesObj? "}" ;
ParesObj           -> ParObj ("," ParObj)* ;
ParObj             -> (Ident | TextoLiteral) ":" Expressao ;

EstruturaArray     -> "[" ItensArr? "]" ;
ItensArr           -> Expressao ("," Expressao)* ;
```

---

## 🏗️ **Classificação na Hierarquia de Chomsky**

- **Tipo 2 – Livre de Contexto (G2)**: todas as produções têm **um único não-terminal** à esquerda (`A → α`).  
  - Suporta estruturas aninhadas (`Bloco`, parênteses), precedência por estratos (`Add/Mul/Exp`), e controle de fluxo.  
- **Não é G3 (Regular)**: pilha é necessária para `{}`/`()` aninhados.  
- **Evolução planejada para G1 (Sensível ao Contexto)**: impor **coerência de tipos** e restrições dependentes de ambiente (e.g., `return` compatível com tipo, uso de identificadores declarados, proibição de atribuições inválidas).

### 🔍 Limitações da Gramática e Análise Semântica

- **G2 não “lembra” contexto**: não garante que `Ident` foi previamente declarado, nem que `a: numerus` receba valor `textus`.  
- **Solução**: fase de **Análise Semântica** com **tabela de símbolos** e **verificador de tipos**. Opcionalmente, modelar como **G1** com famílias `Expressao[T]` e reescritas contextuais (αAβ → αγβ) para **propagar tipos**.

---

## 🔍 **Resolução de Ambiguidades**

### **Problemas Identificados e Soluções**

1) **Precedência e associatividade**  
   - Estratificação clássica: `Exp` > `Mul` > `Add` > `Rel` > `Igual` > `Coalesc ??` > `&&` > `||` > `?:` > atribuições.  
   - `**` é **associativo à direita**; `+ - * /` à **esquerda**; comparações **não associativas** em cadeia (emitir erro).

2) **Dangling else** (`si … aliter`)  
   - Regra sintática já **acopla** `aliter` ao `si` **mais próximo** via `InstrucaoIf` recursiva à direita.  
   - Em geradores LL/LR, manter **preferência** ao shift de `aliter` para o `si` imediatamente aberto.

3) **Declaração vs expressão**  
   - `DeclaracaoVar` e `Expressao` são alternativas distintas em `Instrucao` e em `CabecaFor` com `ForInitOpt`, removendo ambiguidade.

---

## 🧪 **Exemplos de Derivação**

### **Programa simples com condicional**
Código (Scriptum):
```js
mutabilis i: numerus = 18;
si (i >= 18) { redde; } aliter { redde; }
```

Derivação (esboço):
```
Programa ⇒ Elemento* ⇒ Declaracao ";" InstrucaoIf
Declaracao ⇒ DeclaracaoVar ⇒ mutabilis Ident : Tipo = Expressao
… ⇒ mutabilis i : numerus = ExpressaoAtrib ⇒ … ⇒ 18
InstrucaoIf ⇒ si "(" Expressao ")" Instrucao ("aliter" Instrucao)?
⇒ si "(" ExpressaoRel ")" Instrucao "aliter" Instrucao
⇒ si "(" i >= 18 ")" Bloco "aliter" Bloco
```

### **Programa com função**

```js
functio addere(a: numerus, b: numerus): numerus {
  redde a + b;
}

mutabilis r: numerus = addere(5, 3);
```

Derivação (parcial):
```
Elemento ⇒ DeclaracaoFuncao
⇒ functio Ident ParametrosFunc TipoRetornoOpt Bloco
⇒ functio addere "(" Parametro "," Parametro ")" ":" Tipo Bloco
⇒ …
Elemento ⇒ Declaracao ⇒ DeclaracaoVar ⇒ mutabilis r : numerus = ExpressaoAtrib
⇒ … ⇒ ExpressaoPostfix ⇒ Ident Chamada ⇒ addere "(" 5 "," 3 ")"
```

---

## 🎯 **Características Específicas da Scriptum**

- **Palavras‑chave latinas** e **tipagem explícita** (`: Tipo`).  
- **Encadeamentos JS‑like**: `obj?.prop[0](x)` por `OpcionalChain`, `AcessoPonto`, `AcessoIndexado`, `Chamada`.  
- **Estruturas de tipo**: `TipoObjeto` estrutural (`{ campo: Tipo }`), `TipoArray`, `TipoFuncao` com genéricos `functio<T>(...) -> R` (na gramática, semântica posterior).

---

## 📊 **Validação e Testes**

### **Programas de teste criados**

**Teste 1 — Declaração tipada e expressão aritmética**
```js
mutabilis x: numerus = (10 + 2) * 3;
```

**Teste 2 — Condicional com else**
```js
constans nome: textus = "Marcus";
si (nome == "Marcus") redde; aliter redde;
```

**Teste 3 — Função e chamada**
```js
functio area(r: numerus): numerus { redde 3.14 * r * r; }
mutabilis a: numerus = area(2);
```

**Teste 4 — For-of (de) e objeto**
```js
mutabilis acc: numerus = 0;
pro (mutabilis v: numerus de [1,2,3]) { acc = acc + v; }
```

### **Análise de erros sintáticos (esperados)**

- Falta de `;` ao fim de instrução simples.  
- `aliter` sem `si` correspondente.  
- Parênteses/chaves colchetes não balanceados.  
- `pro` clássico com cabeçalho inválido: `pro (; ; )` (permitido mas inútil — semântico).

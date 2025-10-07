# Entrega: Léxico e Tratamento de Erros da Linguagem **Scriptum** 📝

> Integração da gramática formal (G2) com a especificação léxica baseada em expressões regulares. Inclui: regex por token, análise de ambiguidades, estratégias de erro e mensagens ao usuário.

---

## 1) 🔤 Especificação Completa via Expressões Regulares

- **Identificadores**  
```regex
IDENT => [\p{L}_][\p{L}\p{M}\p{N}_]*   (Unicode NFC)
```

- **Palavras-chave**  
```regex
KW => \b(mutabilis|constans|functio|classis|structor|novum|hoc|super
|si|aliter|dum|pro|in|de|redde|frange|perge
|verum|falsum|nullum|indefinitum
|numerus|textus|booleanum|vacuum|quodlibet)\b
```

- **Números**  
```regex
INT_DEC => (0|[1-9](_?[0-9])*)  
FLOAT   => ([0-9](_?[0-9])*\.[0-9](_?[0-9])*)([eE][+-]?[0-9](_?[0-9])*)?
```

- **Strings**  
```regex
TEXTO => "(?:[^"\\\r\n]|\\.)*"
```

- **Comentários**  
```regex
LINE_COMMENT  => //[^\r\n]*  
BLOCK_COMMENT => /\*[^*]*\*+(?:[^/*][^*]*\*+)*/  
```

- **Operadores e delimitadores**  
```regex
OP  => (===|!==|==|!=|<=|>=|\*\*|&&|\|\||\?\?|\?\.|\+=|-=|\*=|/=|%=|=|<|>|!|\+|-|\*|/|%)  
DELIM => [()\[\]{};,.:?]  
ARROW => ->
```

---

## 2) ⚖️ Análise de Ambiguidades e Regras de Resolução

- **Ident vs Keyword** → palavras-chave têm precedência; `IDENT` reclassificado se ∈ KW.  
- **Float vs Int vs "."** → `123.` e `.5` são FLOAT; `.` isolado é DELIM.  
- **`?` vs `??` vs `?.`** → resolver por ordem: `??` > `?.` > `?`.  
- **Operadores compostos** → aplicar **maximal munch** (maior comprimento primeiro).  
- **Dangling else (`si … aliter`)** → `aliter` associa ao `si` mais próximo (regra recursiva à direita na gramática).  
- **Associações** → `**` é à direita; `+ - * /` à esquerda; comparações não encadeiam (`a < b < c` gera erro semântico).

---

## 3) 🚨 Estratégia de Tratamento de Erros Léxicos

- **Caractere inválido**  
  - Consome 1 codepoint, emite `LEX001_INVALID_CHAR`.  
- **Comentário de bloco não terminado**  
  - `LEX010_UNTERMINATED_COMMENT` até EOF.  
- **String não terminada**  
  - `LEX020_UNTERMINATED_STRING` até quebra de linha.  
- **Escape inválido em string**  
  - `LEX021_INVALID_ESCAPE`.  
- **Número malformado** (underscore duplo, expoente sem dígito)  
  - `LEX030_MALFORMED_NUMBER`.  
- **Sequência de operador inválida** (`?=` não suportado)  
  - `LEX040_BAD_OPERATOR_SEQUENCE`.

**Política**: recuperação local sem abortar parsing; acumulam-se diagnósticos até limite configurável.

---

## 4) 💬 Mensagens de Erro — Esboços

Formato: `[CÓDIGO] Mensagem` + **localização** + snippet com caret.

### Exemplo 1 — String não terminada
```
[LEX020] String não terminada
→ linha 7, coluna 15
7 | constans s: textus = "salve, mundus
                              ^ falta aspas de fechamento
Dica: feche a string com ".
```

### Exemplo 2 — Número malformado
```
[LEX030] Número inválido: "1__23"
→ linha 4, coluna 10
4 | mutabilis x: numerus = 1__23;
                           ^^ underscore duplicado
Dica: use apenas um '_' entre dígitos.
```

### Exemplo 3 — Caractere inválido
```
[LEX001] Caractere inválido: '@'
→ linha 2, coluna 5
2 | mutabilis @x: numerus = 10;
             ^
Dica: ident deve iniciar com letra ou '_'.
```

---

## 5) 📊 Validação e Testes Mínimos

- Casos válidos:  
  - `mutabilis x: numerus = 3.14;`  
  - `si (x >= 10) redde; aliter { perge; }`  
- Casos de erro:  
  - `"string sem fim` → `LEX020`  
  - `1__23` → `LEX030`  
  - `?=` → `LEX040`

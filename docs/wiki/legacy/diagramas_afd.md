# Diagramas de AFDs da Linguagem Scriptum
 
Cada diagrama abaixo utiliza notação Mermaid (`stateDiagram-v2`) para representar a automação determinística resultante das expressões regulares.

## WHITESPACE
```mermaid
stateDiagram-v2
    [*] --> S0
    S0 --> S1 : espacio/tab/FEFF/\n/\r
    S1 --> S1 : espacio/tab/FEFF/\n/\r
    S1 --> [*]
```

## COMMENT_LINE (`//...`)
```mermaid
stateDiagram-v2
    [*] --> S0
    S0 --> S1 : '/'
    S1 --> S2 : '/'
    S2 --> S2 : qualquer_exceto_\n_\r
    S2 --> [*]
```

## COMMENT_BLOCK (`/* ... */`)
```mermaid
stateDiagram-v2
    [*] --> B0
    B0 --> B1 : '/'
    B1 --> B2 : '*'
    B2 --> B2 : not('*')
    B2 --> B3 : '*'
    B3 --> B3 : '*'
    B3 --> B2 : not('/')
    B3 --> B4 : '/'
    B4 --> [*]
```

## IDENTIFIER
```mermaid
stateDiagram-v2
    [*] --> I0
    I0 --> I1 : '_' | XID_Start
    I1 --> I1 : '_' | XID_Continue
    I1 --> [*]
```

## KEYWORDS
```mermaid
stateDiagram-v2
  direction LR
  [*] --> K0
  K0 --> K1: m
  K1 --> K2: u
  K2 --> K3: t
  K3 --> K4: a
  K4 --> K5: b
  K5 --> K6: i
  K6 --> K7: l
  K7 --> K8: i
  K8 --> K9: s
  state K9 <<accept>>
  K9 --> [*]
```

## INT_DECIMAL
```mermaid
stateDiagram-v2
    [*] --> D0
    D0 --> D1 : '0'
    D0 --> D2 : '1'-'9'
    D2 --> D2 : '0'-'9'
    D2 --> D3 : '_'
    D3 --> D2 : '0'-'9'
    D1 --> [*]
    D2 --> [*]
```

## INT_BINARY
```mermaid
stateDiagram-v2
    [*] --> B0
    B0 --> B1 : '0'
    B1 --> B2 : 'b'
    B2 --> B3 : '0'|'1'
    B3 --> B3 : '0'|'1'
    B3 --> B4 : '_'
    B4 --> B3 : '0'|'1'
    B3 --> [*]
```

## INT_OCTAL
```mermaid
stateDiagram-v2
    [*] --> O0
    O0 --> O1 : '0'
    O1 --> O2 : 'o'
    O2 --> O3 : '0'-'7'
    O3 --> O3 : '0'-'7'
    O3 --> O4 : '_'
    O4 --> O3 : '0'-'7'
    O3 --> [*]
```

## INT_HEX
```mermaid
stateDiagram-v2
    [*] --> H0
    H0 --> H1 : '0'
    H1 --> H2 : 'x'
    H2 --> H3 : hex
    H3 --> H3 : hex
    H3 --> H4 : '_'
    H4 --> H3 : hex
    H3 --> [*]
```

## FLOAT_DECIMAL
```mermaid
stateDiagram-v2
    [*] --> F0
    F0 --> F1 : digits
    F0 --> F2 : '.'
    F1 --> F1 : digits/_digits
    F1 --> F3 : '.'
    F1 --> F5 : 'e'|'E'
    F3 --> F4 : digits
    F4 --> F4 : digits/_digits
    F4 --> F5 : 'e'|'E'
    F2 --> F4 : digits
    F5 --> F6 : '+'|'-'
    F5 --> F7 : digits
    F6 --> F7 : digits
    F7 --> F7 : digits/_digits
    F4 --> [*]
    F7 --> [*]
    F3 --> [*]
```

## NUMERIC_LITERAL (com sufixo opcional)
```mermaid
stateDiagram-v2
    [*] --> NL0
    NL0 --> NL1 : via_float|int
    NL1 --> NL2 : 'f'|'F'
    NL2 --> NL3 : '32'|'64'
    NL1 --> [*]
    NL3 --> [*]
```

## STRING_LITERAL
```mermaid
stateDiagram-v2
    [*] --> S0
    S0 --> S1 : '"'
    S1 --> S1 : texto
    S1 --> S2 : '\\'
    S2 --> S1 : escape_simples
    S2 --> S3 : 'x'
    S3 --> S4 : hex
    S4 --> S1 : hex
    S2 --> S5 : 'u'
    S5 --> S6 : '{'
    S6 --> S6 : hex (1-6)
    S6 --> S1 : '}'
    S1 --> S7 : '"'
    S7 --> [*]
```

## OPERATORS
```mermaid
stateDiagram-v2
  direction LR
  [*] --> Ope0

  %% 1º caractere: classe de operadores e pontuação relevante
  Ope0 --> Ope1: &#42; | &#61; | &#33; | &#60; | &#62; | &#38; | &#124; | &#63; | &#43; | &#45; | &#47; | &#37; | &#58;

  %% 2º caractere (tokens duplos): ==, !=, <=, >=, &&, ||, ??, +=, -=, *=, /=, %=, :=
  Ope1 --> Ope2: segundo_caractere

  %% 3º caractere (tokens triplos): ===, !==
  Ope2 --> Ope3: terceiro_caractere

  %% Aceitações por comprimento
  Ope1 --> [*]
  Ope2 --> [*]
  Ope3 --> [*]
```

## DELIMITERS
```mermaid
stateDiagram-v2
  [*] --> L0
  L0 --> [*] : PONTUACAO

  note right of L0
    PONTUACAO = , ; . ( ) [ ] { }
  end note
```

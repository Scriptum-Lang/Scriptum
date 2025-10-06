# Fluxo de Análise Léxica

1. Carrega `SourceMap` do arquivo `.stm`.
2. Usa `memchr` para localizar separadores rapidamente.
3. Identifica tokens via DFAs especializados (identificadores, números, operadores).
4. Emite `Token`s imutáveis com `Span` compacta.

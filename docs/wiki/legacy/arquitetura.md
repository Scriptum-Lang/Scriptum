# Arquitetura do Compilador Scriptum

O compilador Scriptum é organizado em camadas modulares que espelham as fases
tradicionais de um pipeline de compilação. Cada fase é implementada como uma
crate independente do Rust, permitindo reuso e testes isolados.

1. **Lexer (`scriptum-lexer`)**: converte texto `.stm` em tokens otimizados.
2. **Parser (`scriptum-parser-ll`)**: consome tokens via um analisador LL(1)
   gerado a partir da gramática em `docs/especificacao-linguagem.md`.
3. **AST (`scriptum-ast`)**: estrutura de dados imutável com interning de
   identificadores e `Span`s leves.
4. **Semântica (`scriptum-sema`)**: checagem de tipos, escopos e coerções.
5. **Codegen (`scriptum-codegen`)**: geração de IR SSA-like e otimizações.
6. **Runtime (`scriptum-runtime`)**: máquina virtual interpretativa e loader
   de bytecode `.sbc`.
7. **CLI (`scriptum-cli`)**: interface de linha de comando centrada em DX.

Os módulos são conectados por tipos compartilhados em `scriptum-utils`, que
oferece `SourceMap`, diagnósticos com Ariadne/Miette e spans compactos.

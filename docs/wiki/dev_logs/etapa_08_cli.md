# Etapa 08 — CLI funcional

## Comandos disponíveis
- `scriptum version`: exibe a versão atual do pacote CLI.
- `scriptum build-lexer [--show]`: regenera `lexer/tables.json` a partir das ERs; `--show` imprime o JSON no terminal.
- `scriptum lex <arquivo.stm> [--no-skip-whitespace]`: tokeniza o arquivo mostrando o tipo e lexema (p. ex. `scriptum lex examples/ok/basicos/variaveis.stm`).
- `scriptum parse <arquivo.stm> [--dump-ast]`: executa o parser; com `--dump-ast` imprime a AST em JSON (ex.: `scriptum parse examples/ok/intermediarios/classes.stm --dump-ast`).
- `scriptum run <arquivo.stm>`: placeholder que confirma o parse e avisa que a execução ainda não foi implementada.

## Exemplos
- `scriptum version` ? `Scriptum CLI version 0.1.0`
- `scriptum lex examples/ok/basicos/variaveis.stm` ? mostra tokens `functio`, `init`, etc.
- `scriptum parse examples/err/negativos/tipo_incompativel.stm --dump-ast` ? imprime AST serializada (sem análise semântica automática por enquanto).

# Scriptum Lexer

Esta etapa do projeto entrega o analisador léxico da linguagem Scriptum.

## Pré-requisitos

- [Rust](https://www.rust-lang.org/) instalado (versão 1.70 ou superior).

## Como executar

1. Entre na pasta `scriptum` na raiz do repositório:

   ```bash
   cd scriptum
   ```

2. Rode o analisador léxico apontando para um arquivo fonte `.scriptum`:

   ```bash
   cargo run -p scriptum-lexer -- examples/programa.scriptum
   ```

   A saída exibirá uma tabela com duas colunas (`TOKEN` e `TIPO`) listando todos os lexemas reconhecidos.

3. Caso deseje apenas gerar os diagramas dos autômatos determinísticos, execute:

   ```bash
   cargo run -p scriptum-lexer -- --emit-diagrams
   ```

### Exemplo

Utilizando o arquivo `examples/programa.scriptum`, o comando anterior gera uma tabela semelhante a:

```
TOKEN                          | TIPO
-----------------------------------------------------
mutabilis                      | Keyword(mutabilis)
numerus_principal              | IDENT
:                              | COLON
numerus                        | Keyword(numerus)
=                              | EQUAL
3                              | NUMBER
;                              | SEMICOLON
...
```

## Tratamento de erros léxicos

Caso o analisador encontre um símbolo inválido, o programa interrompe a análise e exibe a linha e a coluna exatas do erro, além de destacar o trecho problemático.

# Scriptum Wiki

Bem-vindo ao hub de documentacao oficial da linguagem **Scriptum** (`.stm`). Aqui voce encontra a visao geral do projeto, as especificacoes formais e as diretrizes de contribuicao.

## Conteudo principal

1. [Gramatica e sintaxe](01_gramatica.md)
2. [Lexico e tokens](02_lexico.md)
3. [Arquitetura do parser](03_parser.md)
4. [Arvore de Sintaxe Abstrata (AST)](04_ast.md)
5. [Tipos e analise semantica](05_tipos_semantica.md)
6. [IR, codegen e pipeline de build](06_ir_codegen.md)
7. [Fluxo completo do compilador](07_fluxo_compilador.md)
8. [Pipeline do lexer](08_lexer_pipeline.md)
9. [Parser e AST passo a passo](09_parser_ast_pipeline.md)
10. [Analise semantica passo a passo](10_semantica_pipeline.md)
11. [AFN e AFD no lexer](11_afn_afd.md)
12. [Roadmap e evolucoes](99_roadmap.md)

## Estrutura do repositorio

```
.
|- docs/
|  |- wiki/
|- examples/
|- scriptum/
|  |- pyproject.toml
|  |- README.md
|  |- scripts/
|  |- src/scriptum/
|  |  |- ast/
|  |  |- codegen/
|  |  |- lexer/
|  |  |- parser/
|  |  |- regex/
|  |  |- sema/
|  |  |- text.py
|  |  |- tokens.py
|  |  |- driver.py
|  |- tests/
|- LICENSE
```

## Convenicoes de contribuicao

- Utilize Python 3.11+ com `ruff`, `black` e `pytest` antes de enviar PRs (scripts auxiliares estao em `scriptum/scripts/`).
- Atualize a documentacao quando alterar gramaticas, tokens ou fases do compilador. Mudancas no lexer devem refletir ajustes em `docs/wiki/08_lexer_pipeline.md`, por exemplo.
- Diagnosticos devem citar `Span` e, quando possivel, incluir codigo de erro previsivel.
- Testes unitarios ficam proximos dos modulos em `scriptum/tests`.

## Documentacao legada

Materiais de versoes anteriores estao em [`docs/wiki/legacy/`](legacy/). Consulte-os apenas como referencia historica; o conteudo desta wiki tem prioridade.

Boa leitura e bons commits!

# Roadmap (99)

## Entregas atuais
- Lexer determinístico com geração de tabelas (`scripts/build_afd.py`) e CLI (`scriptum lex`).
- Parser híbrido (Pratt + declarações) com AST tipada e suporte à CLI (`scriptum parse`).
- Analisador semântico inicial: tabela de símbolos, verificador de tipos básico e diagnósticos.
- Suite de testes cobrindo lexing, parsing e semântica (`pytest -q`).

## Próximos passos (curto prazo)
- Integrar análise semântica à CLI (`scriptum sema` ou `scriptum run`).
- Expandir verificação de tipos: chamadas de função, objetos e arrays tipados.
- Adicionar testes automatizados para diagnósticos negativos adicionais.

## Médio prazo
- Implementar IR (`06_ir_codegen.md`) e comando `--emit-ir`.
- Começar o módulo de codegen / interprete básico (`scriptum run`).
- Ferramentas de lint (variáveis não utilizadas, importações).

## Longo prazo
- Backend de bytecode com otimizador (propagação de constantes, DCE, SSA optional).
- Servidor LSP com diagnósticos incrementais.
- Suporte a módulos multi-arquivo e documentação automática (`scriptum doc`).
- Targets avançados (LLVM/WASM) e integração contínua.

Sugestões continuam bem-vindas — abra uma issue com a tag `enhancement` ou participe das reuniões quinzenais do projeto.

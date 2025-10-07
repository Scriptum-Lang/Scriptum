# Scriptum Compiler (Python)

Scriptum é uma linguagem com sintaxe inspirada em JavaScript, palavras-chave em latim e tipagem explícita. Este repositório contém a implementação do compilador em Python 3.11+, seguindo as especificações documentadas em `docs/wiki/`.

## Estrutura

- `src/scriptum/`: código-fonte principal (CLI, driver, léxico, parser, AST, semântica, IR/codegen).
- `scripts/`: utilitários para geração de autômatos e automação de commits.
- `tests/`: suíte de testes (fixtures compartilhados ficam em `tests/fixtures/`).
- `docs/`: documentação de referência e logs de desenvolvimento.
- `examples/`: amostras de programas Scriptum válidos e inválidos.

## Ambiente de desenvolvimento

Instale as dependências e ative o Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Rodar testes

```bash
pytest
```

### CLI

```bash
scriptum --help
```

## Próximos passos

1. Implementar o lexer com base nos DFAs descritos em `docs/wiki/02_lexico.md`.
2. Construir o parser (descida recursiva + Pratt) conforme `docs/wiki/03_parser.md`.
3. Popular AST, semântica, IR e codegen.

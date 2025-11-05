# Scriptum Compiler (Python)

Scriptum é uma linguagem com sintaxe inspirada em JavaScript, palavras-chave em latim e tipagem explícita. Este repositório contém a implementação do compilador em Python 3.11+, seguindo as especificações documentadas em `docs/wiki/`.

## Estrutura

- `src/scriptum/`: código-fonte principal (CLI, driver, léxico, parser, AST, semântica, IR/codegen).
- `scripts/`: utilitários para geração de autômatos e automação de commits.
- `tests/`: suíte de testes (fixtures compartilhados ficam em `tests/fixtures/`).
- `docs/`: documentação de referência e logs de desenvolvimento.
- `examples/`: amostras de programas Scriptum válidos e inválidos.

## Ambiente de desenvolvimento

Instale as dependências e prepare o ambiente Python 3.11+ da forma que preferir:

---

### Opção 1: Usando `pip` e `venv` (Padrão)

1. **Crie um ambiente virtual**
   ```bash
   python -m venv .venv
   ```

2. **Ative o ambiente virtual**
   - **Windows**
     ```powershell
     .\.venv\Scripts\activate
     ```
   - **macOS/Linux**
     ```bash
     source .venv/bin/activate
     ```

3. **Instale o Scriptum em modo desenvolvimento**
   ```bash
   pip install -e ".[dev]"
   ```

---

### Opção 2: Usando `uv` (Alternativa Rápida)

1. **Sincronize o ambiente automaticamente**
   ```bash
   uv sync
   ```

   O `uv` criará o ambiente virtual (por padrão em `.venv`) e instalará todas as dependências, incluindo as extras de desenvolvimento.

2. **Execute comandos no ambiente**
   - Prefira chamar ferramentas diretamente:
     ```bash
     uv run pytest
     ```
   - Se desejar ativar o ambiente manualmente:
     - **Windows**
       ```powershell
       .\.venv\Scripts\activate
       ```
     - **macOS/Linux**
       ```bash
       source .venv/bin/activate
       ```
     Depois basta rodar:
     ```bash
     pytest
     ```

### Rodar testes

```bash
pytest
```

### CLI

```bash
scriptum --help
```

> Nota: o analisador léxico normaliza entradas para o formulário NFKC e substitui caracteres fora de ASCII por espaços, garantindo que fontes com acentuação sejam aceitas sem falhas.
> Nota 2: os comandos que recebem arquivos verificam a extensão `.stm` e falham com uma mensagem clara quando o caminho não segue o padrão.

### Instalação global (`pipx`)

Para manter o compilador isolado do Python do sistema:

```bash
pipx install .
```

Após a instalação, os comandos abaixo funcionam de forma idêntica em Windows, macOS e Linux:

- `scriptum --help`
- `python -m scriptum`
- `python -m scriptum.cli --help`

### Execução multiplataforma

Depois de clonar o repositório e preparar o ambiente (`uv sync` ou `pip install -e .`), valide:

```bash
uv run scriptum --help
uv run python -m scriptum --help
uv run python -m scriptum.cli lex examples/ok/loops_and_funcs.stm
```

Os mesmos comandos funcionam trocando `uv run` por `python -m venv .venv && .\.venv\Scripts\python` (Windows) ou `source .venv/bin/activate` (macOS/Linux) caso esteja usando `pip` puro.

### Exemplos rápidos

Tokenizar um programa válido:

```bash
scriptum lex examples/ok/loops_and_funcs.stm
```

Compilar e interromper após o parser:

```bash
scriptum compile examples/ok/loops_and_funcs.stm --stage parser
```

## Próximos passos

1. Implementar o lexer com base nos DFAs descritos em `docs/wiki/02_lexico.md`.
2. Construir o parser (descida recursiva + Pratt) conforme `docs/wiki/03_parser.md`.
3. Popular AST, semântica, IR e codegen.

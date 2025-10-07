# Etapa 05 — Lexer determinístico

## Implementação
- Carregamento das tabelas DFA (`lexer/tables.json`) em `ScriptumLexer`, convertendo estados para transições determinísticas com informações de aceitação.
- Estratégia **maximal munch** com precedência: palavras-chave reconhecidas a partir do padrão de identificador e reclassificadas (`tokens.is_keyword`).
- Tokens transportam `Span`, lexema e valor decodificado (números sem `_`, strings com `unicode_escape`). Comentários e espaços são ignorados por padrão, mas podem ser emitidos via `--no-skip-whitespace`.
- Erros léxicos são propagados como `errors.LexerError`, incluindo posição e mensagem amigável.

## Geração e uso
- Regerar tabelas do lexer:
  ```bash
  scriptum build-lexer --show
  ```
- Analisar um arquivo e listar tokens:
  ```bash
  scriptum lex examples/ok/basicos/variaveis.stm
  ```
- A CLI continua oferecendo `scriptum compile` para pipeline completo (etapas futuras).

## Testes
- Casos positivos com exemplos reais (`examples/ok/basicos/*.stm`) validam sequência e classificação de tokens.
- Casos negativos (`tests/test_lexer_errors.py`) cobrem caracteres inválidos e strings não terminadas.
- Suite principal:
  ```bash
  pytest -q tests/test_lexer_tokens.py
  pytest -q tests/test_lexer_errors.py
  ```

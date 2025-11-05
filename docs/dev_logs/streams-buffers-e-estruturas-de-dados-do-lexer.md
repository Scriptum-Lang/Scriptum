# Streams, buffers e estruturas de dados do Lexer

- **Principio do match mais longo** - [src/scriptum/lexer/lexer.py#L120](../../src/scriptum/lexer/lexer.py#L120): o metodo `_match_token` percorre a DFA mantendo o ultimo estado de aceitacao valido para devolver sempre o lexema mais longo (desempate pela prioridade do padrao).
- **Estrutura do token** - [src/scriptum/tokens.py#L17](../../src/scriptum/tokens.py#L17) e [src/scriptum/tokens.py#L90](../../src/scriptum/tokens.py#L90): o enum `TokenKind` concentra as classes lexicas e o dataclass `Token` agrega `lexeme`, `span`, `value` e metadados consumidos pelas etapas seguintes.
- **Bufferizacao** - [src/scriptum/lexer/lexer.py#L54](../../src/scriptum/lexer/lexer.py#L54): `ScriptumLexer.tokenize` le `text_data` como buffer unico, avanca `position` enquanto acumula tokens em `result` e encerra com o marcador `EOF`.
- **Integracao com analise sintatica** - [src/scriptum/parser/parser.py#L43](../../src/scriptum/parser/parser.py#L43) e [src/scriptum/parser/parser.py#L54](../../src/scriptum/parser/parser.py#L54): `ScriptumParser` instancia `ScriptumLexer` e consome `_tokens` tokenizados antes de iniciar o parsing.

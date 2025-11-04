from __future__ import annotations

from pathlib import Path

from scriptum import tokens
from scriptum.lexer import spec
from scriptum.lexer.lexer import ScriptumLexer
from scriptum.regex.builder import AutomataBuilder
from scriptum.text import SourceFile

EXAMPLES_ROOT = Path(__file__).resolve().parents[2] / "examples"


def _load_source(relative: Path) -> SourceFile:
    path = EXAMPLES_ROOT / relative
    return SourceFile(str(path), path.read_text(encoding="utf8"))


def test_keywords_are_lowercase_and_unique() -> None:
    assert len(tokens.KEYWORDS) == len(set(tokens.KEYWORDS))
    for keyword in tokens.KEYWORDS:
        assert keyword == keyword.lower()


def test_token_patterns_metadata_consistency() -> None:
    payload = spec.to_json()
    assert payload["keywords"] == list(tokens.KEYWORDS)
    assert payload["version"] == 1
    assert all(entry["pattern"] for entry in payload["token_patterns"])


def test_automata_builder_generates_accepting_states() -> None:
    builder = AutomataBuilder()
    result = builder.build(spec.TOKEN_PATTERNS)
    assert result.dfa.states, "DFA should contain states"
    accepting_indices = {state.accepting.index for state in result.dfa.states if state.accepting}
    assert accepting_indices == set(range(len(spec.TOKEN_PATTERNS)))


def test_literal_patterns_present() -> None:
    literal_patterns = {
        entry.pattern for entry in spec.TOKEN_PATTERNS if entry.kind in (tokens.TokenKind.OPERATOR, tokens.TokenKind.PUNCTUATION, tokens.TokenKind.DELIMITER)
    }
    for literal in tokens.all_literals():
        escaped = spec.literal_regex(literal)
        assert escaped in literal_patterns, f"Literal {literal!r} missing from specification"


def test_variaveis_program_tokens() -> None:
    lexer = ScriptumLexer()
    source = _load_source(Path("ok/basicos/variaveis.stm"))
    token_stream = lexer.tokenize(source)
    filtered = [tok for tok in token_stream if tok.kind is not tokens.TokenKind.EOF]

    first_segment = [(filtered[i].kind, filtered[i].lexeme) for i in range(12)]
    assert first_segment == [
        (tokens.TokenKind.KEYWORD, "functio"),
        (tokens.TokenKind.IDENTIFIER, "init"),
        (tokens.TokenKind.DELIMITER, "("),
        (tokens.TokenKind.DELIMITER, ")"),
        (tokens.TokenKind.PUNCTUATION, "->"),
        (tokens.TokenKind.KEYWORD, "numerus"),
        (tokens.TokenKind.DELIMITER, "{"),
        (tokens.TokenKind.KEYWORD, "mutabilis"),
        (tokens.TokenKind.KEYWORD, "numerus"),
        (tokens.TokenKind.IDENTIFIER, "a"),
        (tokens.TokenKind.OPERATOR, "="),
        (tokens.TokenKind.NUMBER_LITERAL, "1"),
    ]


def test_keyword_is_prioritized_over_identifier() -> None:
    lexer = ScriptumLexer()
    source = SourceFile(None, "mutabilis mutabilis1")
    tokens_out = lexer.tokenize(source)
    assert tokens_out[0].kind is tokens.TokenKind.KEYWORD
    assert tokens_out[1].kind is tokens.TokenKind.IDENTIFIER


def test_err_example_contains_string_literal_value() -> None:
    lexer = ScriptumLexer()
    source = _load_source(Path("err/negativos/tipo_incompativel.stm"))
    tokens_out = lexer.tokenize(source)
    string_tokens = [tok for tok in tokens_out if tok.kind is tokens.TokenKind.STRING_LITERAL]
    assert string_tokens
    assert string_tokens[0].value == "texto"


def _tokenize_inline(text: str) -> list[tokens.Token]:
    lexer = ScriptumLexer()
    tokens_out = lexer.tokenize(SourceFile(None, text))
    return [tok for tok in tokens_out if tok.kind is not tokens.TokenKind.EOF]


def test_power_operator_is_lexed_as_single_token() -> None:
    tokens_out = _tokenize_inline("a ** b ** c")
    operators = [tok.lexeme for tok in tokens_out if tok.kind is tokens.TokenKind.OPERATOR]
    assert operators == ["**", "**"]


def test_logical_and_comparison_operators() -> None:
    snippet = "a ?? b ?: c || d && e == f != g === h !== i > j >= k < l <= m"
    tokens_out = _tokenize_inline(snippet)
    operator_tokens = [tok.lexeme for tok in tokens_out if tok.kind is tokens.TokenKind.OPERATOR]
    assert operator_tokens == ["??", "?:", "||", "&&", "==", "!=", "===", "!==", ">", ">=", "<", "<="]


def test_punctuation_and_delimiters() -> None:
    snippet = ":: -> => , ; : ? { } [ ] ( ) obj.prop"
    tokens_out = _tokenize_inline(snippet)
    punctuation = [tok.lexeme for tok in tokens_out if tok.kind is tokens.TokenKind.PUNCTUATION]
    delimiters = [tok.lexeme for tok in tokens_out if tok.kind is tokens.TokenKind.DELIMITER]
    dot_tokens = [tok.lexeme for tok in tokens_out if tok.kind is tokens.TokenKind.OPERATOR and tok.lexeme == "."]
    assert punctuation == ["::", "->", "=>", ",", ";", ":", "?"]
    assert delimiters == ["{", "}", "[", "]", "(", ")"]
    assert dot_tokens == ["."]


def test_line_and_block_comments_are_ignored() -> None:
    snippet = "mutabilis numerus a = 1 // linha\nperge = 2; /* bloco */"
    tokens_out = _tokenize_inline(snippet)
    assert all(tok.kind is not tokens.TokenKind.COMMENT for tok in tokens_out)
    assert [tok.lexeme for tok in tokens_out] == ["mutabilis", "numerus", "a", "=", "1", "perge", "=", "2", ";"]

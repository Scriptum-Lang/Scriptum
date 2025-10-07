from __future__ import annotations

from scriptum import tokens
from scriptum.lexer import spec
from scriptum.regex.builder import AutomataBuilder


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

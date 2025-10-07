from __future__ import annotations

import json
from pathlib import Path

import pytest

from scriptum import tokens
from scriptum.lexer import spec


def test_keywords_are_lowercase_and_unique() -> None:
    assert len(tokens.KEYWORDS) == len(set(tokens.KEYWORDS))
    for keyword in tokens.KEYWORDS:
        assert keyword == keyword.lower()


def test_token_patterns_export_to_json(tmp_path: Path) -> None:
    payload = spec.to_json()
    assert payload["keywords"] == list(tokens.KEYWORDS)
    assert payload["version"] == 1

    out_file = tmp_path / "tables.json"
    out_file.write_text(json.dumps(payload))
    assert json.loads(out_file.read_text())["token_patterns"][0]["name"]


@pytest.mark.parametrize("literal", sorted(tokens.all_literals(), key=len, reverse=True))
def test_literals_present_in_patterns(literal: str) -> None:
    patterns = {entry.pattern for entry in spec.TOKEN_PATTERNS if entry.kind in (tokens.TokenKind.OPERATOR, tokens.TokenKind.PUNCTUATION, tokens.TokenKind.DELIMITER)}
    assert literal in {pattern.replace("\\", "") for pattern in patterns}, literal

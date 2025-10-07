from __future__ import annotations

import pytest

from scriptum import errors
from scriptum.lexer.lexer import ScriptumLexer
from scriptum.text import SourceFile


def _source(text: str) -> SourceFile:
    return SourceFile(None, text)


def test_invalid_character_raises_lexer_error() -> None:
    lexer = ScriptumLexer()
    with pytest.raises(errors.LexerError) as captured:
        lexer.tokenize(_source("@"))
    assert captured.value.span.start == 0


def test_unterminated_string_literal() -> None:
    lexer = ScriptumLexer()
    program = 'mutabilis numerus a = "unterminated'
    with pytest.raises(errors.LexerError):
        lexer.tokenize(_source(program))

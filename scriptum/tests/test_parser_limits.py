from __future__ import annotations

import pytest

from scriptum.parser.parser import ParseError, ParserConfig, ScriptumParser
from scriptum.text import SourceFile


def test_parser_depth_limit() -> None:
    config = ParserConfig(max_depth=10)
    parser = ScriptumParser(config=config)
    nested = "(" * 20 + "1" + ")" * 20
    source = SourceFile("<test>", f"functio main() {{ mutabilis numerus x = {nested}; }}")
    with pytest.raises(ParseError):
        parser.parse(source)


def test_parser_depth_limit_can_be_raised() -> None:
    config = ParserConfig(max_depth=1000)
    parser = ScriptumParser(config=config)
    nested = "(" * 50 + "1" + ")" * 50
    source = SourceFile("<test>", f"functio main() {{ mutabilis numerus x = {nested}; }}")
    module = parser.parse(source)
    assert module.declarations

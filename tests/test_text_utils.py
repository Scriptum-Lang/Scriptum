from __future__ import annotations

from scriptum.text import Span, SourceFile, highlight_span, line_col


def test_line_col_and_highlight_from_span() -> None:
    text = "mutabilis numerus x = 1;\nconstans y = x;"
    span = Span(0, 9)
    line, column = line_col(text, span)
    assert (line, column) == (1, 1)
    highlight = highlight_span(text, span)
    assert "mutabilis" in highlight
    assert "^" in highlight


def test_sourcefile_helpers_delegate_to_span() -> None:
    source = SourceFile("<test>", "a\nbc\n")
    span = Span(2, 3)
    line, col = source.line_col(span)
    assert (line, col) == (2, 1)
    snippet = source.highlight(span)
    assert "bc" in snippet

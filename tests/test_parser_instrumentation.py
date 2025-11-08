from __future__ import annotations

from scriptum.parser.parser import ParserTrace, ScriptumParser
from scriptum.text import SourceFile


def test_trace_captures_ll1_derivations() -> None:
    parser = ScriptumParser()
    trace = ParserTrace()
    source = SourceFile("<test>", "mutabilis numerus tmp = 1+2*3;")
    module = parser.parse(source, trace=trace)
    assert module.declarations
    assert trace.expression_trees
    assert any(entry == "ACCEPT" for entry in trace.productions)


def test_trace_logs_general_expression_steps() -> None:
    parser = ScriptumParser()
    trace = ParserTrace()
    source = SourceFile("<test>", "mutabilis numerus tmp = foo(1);")
    parser.parse(source, trace=trace)
    assert any(entry.startswith("CALL") for entry in trace.productions)

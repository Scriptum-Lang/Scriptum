from __future__ import annotations

from scriptum.devtools import ll1_crosscheck


def test_ll1_and_scriptum_parsers_agree_on_basic_expressions() -> None:
    expressions = [
        "42",
        "1+2*3",
        "4-2-1",
        "(1+2)*3-4/2",
        "((2))",
    ]
    reports = ll1_crosscheck.run(expressions)
    assert all(report.success for report in reports)

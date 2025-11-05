from __future__ import annotations

from types import SimpleNamespace

import pytest

from scriptum.regex.builder import AutomataBuilder


def _pattern(name: str, regex: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        pattern=regex,
        kind=SimpleNamespace(name="TOKEN"),
        priority=0,
        ignore=False,
    )


def test_automata_builder_enforces_alphabet_limit() -> None:
    builder = AutomataBuilder(max_alphabet_size=3)
    patterns = [_pattern(chr(ord("a") + idx), chr(ord("a") + idx)) for idx in range(5)]
    with pytest.raises(RuntimeError):
        builder.build(patterns)


def test_automata_builder_enforces_state_limit() -> None:
    builder = AutomataBuilder(max_states=0)
    patterns = [_pattern("WORD", "[a-z]+")]
    with pytest.raises(RuntimeError):
        builder.build(patterns)


def test_automata_builder_timeout() -> None:
    builder = AutomataBuilder(timeout_seconds=0.0)
    patterns = [_pattern("WORD", "[a-z]+")]
    with pytest.raises(TimeoutError):
        builder.build(patterns)

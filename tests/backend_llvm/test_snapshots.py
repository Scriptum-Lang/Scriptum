from __future__ import annotations

from pathlib import Path

import pytest

from scriptum.codegen import generate_llvm
from scriptum.ir import lower_module
from scriptum.parser.parser import ScriptumParser
from scriptum.sema.analyzer import SemanticAnalyzer
from scriptum.text import SourceFile

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "programs"
SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"

SNAPSHOT_CASES = [
    ("basic_valid.stm", "basic_valid.ll"),
    ("loops.stm", "loops.ll"),
    ("arrays.stm", "arrays.ll"),
    ("strings.stm", "strings.ll"),
    ("nullish.stm", "nullish.ll"),
    ("lambdas.stm", "lambdas.ll"),
    ("builtins.stm", "builtins.ll"),
    ("methods.stm", "methods.ll"),
]


def _emit_llvm_from_file(path: Path) -> str:
    parser = ScriptumParser()
    text = path.read_text(encoding="utf8")
    module = parser.parse(SourceFile(str(path), text))
    analysis = SemanticAnalyzer().analyze(module)
    ir_module = lower_module(module, type_info=analysis.type_info, member_bindings=analysis.member_bindings)
    output = generate_llvm(ir_module)
    return output.text.strip()


@pytest.mark.parametrize(("fixture_name", "snapshot_name"), SNAPSHOT_CASES)
def test_snapshot_matches_emitted_ir(fixture_name: str, snapshot_name: str) -> None:
    snapshot_path = SNAPSHOTS / snapshot_name
    assert snapshot_path.exists(), f"snapshot '{snapshot_name}' missing – regen if necessário."
    source = FIXTURES / fixture_name
    current = _emit_llvm_from_file(source)
    expected = snapshot_path.read_text(encoding="utf8").strip()
    assert current == expected, f"LLVM IR diverged from snapshot for {fixture_name}"

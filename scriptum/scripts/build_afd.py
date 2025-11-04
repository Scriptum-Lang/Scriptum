#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera tables.json e o diagrama Mermaid do AFD final."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "scriptum"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from src.scriptum.lexer.spec import TOKEN_SPECS
    from src.scriptum.lexer.afn_to_afd import build_dfa_from_specs
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"Failed to import build dependencies: {exc}") from exc

TABLES = SRC_ROOT / "src" / "scriptum" / "lexer" / "tables.json"
DIAGRAMS_DIR = ROOT / "docs" / "diagramas"
AFD_FINAL_MD = DIAGRAMS_DIR / "afd_final.md"


def emit_mermaid(dfa: dict, path_md: Path) -> None:
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# AFD Final (Mermaid)\n")
    lines.append("```mermaid")
    lines.append("graph LR")

    trans = dfa.get("trans", {})
    for state, edges in trans.items():
        for symbol, target in edges.items():
            label = symbol.replace("\n", "\\n").replace(" ", "\\u00b7")
            lines.append(f'  S{state} -- "{label}" --> S{target}')

    finals = dfa.get("finals", [])
    labels = dfa.get("final_token_labels", {})
    for final_state in finals:
        token_name = labels.get(str(final_state), "")
        lines.append(f"  class S{final_state} final;")
        lines.append(f"  %% final S{final_state} = {token_name}")

    lines.append("classDef final fill:#e0ffe0,stroke:#0a0,stroke-width:1px;")
    lines.append("```")

    path_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    dfa = build_dfa_from_specs(TOKEN_SPECS, deterministic_order=True)

    TABLES.parent.mkdir(parents=True, exist_ok=True)
    TABLES.write_text(json.dumps(dfa, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    emit_mermaid(dfa, AFD_FINAL_MD)

    print(f"[ok] tables.json => {TABLES}")
    print(f"[ok] mermaid     => {AFD_FINAL_MD}")


if __name__ == "__main__":
    main()

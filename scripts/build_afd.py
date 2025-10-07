"""
Generate lexer DFAs from regex specifications.

This script will integrate with the modules under `scriptum.regex` to rebuild
`tables.json`. It currently serves as a placeholder documenting the workflow.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    tables_path = Path(__file__).resolve().parent.parent / "scriptum" / "src" / "scriptum" / "lexer" / "tables.json"
    raise NotImplementedError(f"Automaton generation not yet implemented for {tables_path}")


if __name__ == "__main__":
    main()

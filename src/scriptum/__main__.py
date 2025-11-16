"""Module entry point to invoke the Scriptum CLI with `python -m scriptum`."""

from __future__ import annotations

import importlib
import pathlib
import sys
from types import ModuleType
from typing import Callable


def _resolve_main() -> Callable[[], None]:
    """Import `scriptum.cli.main`, falling back to the source tree when needed."""

    def _import() -> ModuleType:
        return importlib.import_module("scriptum.cli")

    try:
        module = _import()
    except ModuleNotFoundError as exc:
        if exc.name not in {"scriptum", "scriptum.cli"}:
            raise
        package_root = pathlib.Path(__file__).resolve().parent
        candidate = str(package_root.parent)
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
        module = _import()
    return getattr(module, "main")


def run() -> None:
    """Execute the Scriptum CLI."""
    _resolve_main()()


if __name__ == "__main__":
    run()

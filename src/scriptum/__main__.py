"""Module entry point to invoke the Scriptum CLI with `python -m scriptum`."""

from __future__ import annotations

import pathlib
import sys

try:
    from .cli import main  # type: ignore[import]
except ImportError:
    package_root = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(package_root.parent))
    from scriptum.cli import main


def run() -> None:
    """Execute the Scriptum CLI."""
    main()


if __name__ == "__main__":
    run()

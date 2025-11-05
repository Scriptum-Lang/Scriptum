"""Module entry point to invoke the Scriptum CLI with `python -m scriptum`."""

from .cli import main


def run() -> None:
    """Execute the Scriptum CLI."""
    main()


if __name__ == "__main__":
    run()

"""
Command-line interface for the Scriptum compiler.

The CLI is intentionally minimal for now and will expand as the pipeline gains
features. It wires user input to the `CompilerDriver`.
"""

from __future__ import annotations

import pathlib
from typing import Optional

import click

from .driver import CompilerDriver, Stage


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    required=False,
)
@click.option(
    "--stage",
    type=click.Choice([stage.value for stage in Stage]),
    default=Stage.CODEGEN.value,
    help="Pipeline stage to stop after.",
)
def main(source: Optional[pathlib.Path], stage: str) -> None:
    """
    Compile a Scriptum source file.

    SOURCE defaults to stdin when omitted (to be implemented).
    """

    driver = CompilerDriver()
    driver.run(source=source, until=Stage(stage))


if __name__ == "__main__":
    main()

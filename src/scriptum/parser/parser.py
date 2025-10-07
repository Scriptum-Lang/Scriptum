"""
Recursive-descent / Pratt parser scaffold for Scriptum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .. import errors, text, tokens
from ..lexer.lexer import ScriptumLexer


@dataclass(slots=True)
class ParserConfig:
    """Configuration values for the Scriptum parser."""

    allow_lambda_shortcut: bool = True


class ScriptumParser:
    """Parses Scriptum source code into an AST."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        self.config = config or ParserConfig()
        self._lexer = ScriptumLexer()

    def parse(self, source: text.SourceFile) -> None:
        """
        Parse the provided source file and return the root AST node.

        The AST is not defined yet; the function raises until the AST layer is
        implemented and integrated.
        """

        raise errors.CompilerNotImplemented("Parser not yet implemented.")

"""
Scriptum lexer implementation scaffold.

The final lexer will be generated from DFA tables and produce `Token` objects.
For now, the class exposes only the shape of the public API so dependent stages
can be implemented without waiting for the low-level logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Sequence

from .. import errors, text, tokens
from . import spec


@dataclass(slots=True)
class LexerConfig:
    """Configuration object for the Scriptum lexer."""

    skip_whitespace: bool = True


class ScriptumLexer:
    """Tokenizes Scriptum source code."""

    def __init__(self, config: LexerConfig | None = None) -> None:
        self.config = config or LexerConfig()
        self._token_spec = spec.build_default_spec()

    def tokenize(self, source: text.SourceFile) -> List[tokens.Token]:
        """
        Tokenize the provided source file.

        Returns a list ending with an EOF token. The actual lexing logic is not
        implemented yet and will raise until the DFA machinery is ready.
        """

        raise errors.CompilerNotImplemented("Lexer tokenization not yet implemented.")

    def tokenize_iter(self, source: text.SourceFile) -> Iterator[tokens.Token]:
        """Generator variant of `tokenize`."""

        for token in self.tokenize(source):
            yield token

    @property
    def keywords(self) -> Sequence[str]:
        return spec.KEYWORDS

    @property
    def operators(self) -> Sequence[str]:
        return spec.OPERATORS

    @property
    def punctuation(self) -> Sequence[str]:
        return spec.PUNCTUATION

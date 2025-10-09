"""
Deterministic lexer implementation backed by pre-generated DFA tables.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Sequence

from .. import errors, text, tokens


@dataclass(frozen=True, slots=True)
class AcceptEntry:
    index: int
    name: str
    kind: tokens.TokenKind
    priority: int
    ignore: bool


@dataclass(frozen=True, slots=True)
class DFAState:
    transitions: dict[int, int]
    accepting: Optional[AcceptEntry]


@dataclass(frozen=True, slots=True)
class LexerTables:
    start_state: int
    states: List[DFAState]


@dataclass(slots=True)
class LexerConfig:
    """Configuration options controlling lexer behaviour."""

    skip_whitespace: bool = True


class ScriptumLexer:
    """Tokenises Scriptum source code using a deterministic automaton."""

    _TABLES_CACHE: Optional[LexerTables] = None

    def __init__(self, config: LexerConfig | None = None) -> None:
        self.config = config or LexerConfig()
        self._tables = self._load_tables()

    # Public API -----------------------------------------------------------------

    def tokenize(self, source: text.SourceFile) -> List[tokens.Token]:
        """Tokenise *source* into a sequence of Scriptum tokens."""

        result: List[tokens.Token] = []
        text_data = source.text
        position = 0
        length = len(text_data)

        while position < length:
            match = self._match_token(text_data, position)
            if match is None:
                raise self._lex_error(source, position)

            accept, end_pos = match
            lexeme = text_data[position:end_pos]
            span = text.Span(position, end_pos)

            position = end_pos

            if accept.ignore and self.config.skip_whitespace:
                continue

            kind = accept.kind

            if kind is tokens.TokenKind.IDENTIFIER and tokens.is_keyword(lexeme):
                kind = tokens.TokenKind.KEYWORD

            value = self._compute_value(kind, lexeme)
            token = tokens.Token(
                kind=kind,
                lexeme=lexeme,
                span=span,
                value=value,
                metadata={"pattern": accept.name, "index": accept.index},
            )
            result.append(token)

        eof_span = text.Span(length, length)
        result.append(tokens.Token(kind=tokens.TokenKind.EOF, lexeme="", span=eof_span))
        return result

    def tokenize_iter(self, source: text.SourceFile) -> Iterator[tokens.Token]:
        """Iterate lazily over tokens produced from *source*."""

        for token in self.tokenize(source):
            yield token

    @property
    def keywords(self) -> Sequence[str]:
        return tokens.KEYWORDS

    @property
    def operators(self) -> Sequence[str]:
        return tokens.OPERATORS

    @property
    def punctuation(self) -> Sequence[str]:
        return tokens.PUNCTUATION + tokens.DELIMITERS

    # Internal helpers -----------------------------------------------------------

    def _match_token(self, text_data: str, start_pos: int) -> Optional[tuple[AcceptEntry, int]]:
        states = self._tables.states
        state_id = self._tables.start_state
        state = states[state_id]
        index = start_pos
        best_accept: Optional[AcceptEntry] = state.accepting
        best_index = start_pos if state.accepting is None else start_pos
        length = len(text_data)

        while index < length:
            symbol = ord(text_data[index])
            next_state_id = state.transitions.get(symbol)
            if next_state_id is None:
                break
            state = states[next_state_id]
            index += 1
            if state.accepting is not None:
                if best_accept is None or index > best_index or (
                    index == best_index and state.accepting.priority > best_accept.priority
                ):
                    best_accept = state.accepting
                    best_index = index

        if best_accept is None:
            return None
        return best_accept, best_index

    def _compute_value(self, kind: tokens.TokenKind, lexeme: str):
        if kind is tokens.TokenKind.NUMBER_LITERAL:
            sanitized = lexeme.replace("_", "")
            try:
                if "." in sanitized or "e" in sanitized.lower():
                    return float(sanitized)
                return int(sanitized)
            except ValueError:
                return sanitized
        if kind is tokens.TokenKind.STRING_LITERAL:
            inner = lexeme[1:-1]
            try:
                return bytes(inner, "utf8").decode("unicode_escape")
            except UnicodeDecodeError:
                return inner
        return lexeme

    def _lex_error(self, source: text.SourceFile, position: int) -> errors.LexerError:
        line, column = self._line_col(source.text, position)
        char = source.text[position] if position < len(source.text) else "EOF"
        message = f"Unexpected character {char!r} at line {line}, column {column}"
        span = text.Span(position, min(position + 1, len(source.text)))
        return errors.LexerError(message, span)

    @staticmethod
    def _line_col(content: str, pos: int) -> tuple[int, int]:
        line = content.count("\n", 0, pos) + 1
        line_start = content.rfind("\n", 0, pos) + 1
        column = pos - line_start + 1
        return line, column

    @classmethod
    def _load_tables(cls) -> LexerTables:
        if cls._TABLES_CACHE is None:
            path = cls.tables_path()
            try:
                data = json.loads(path.read_text(encoding="utf8"))
            except FileNotFoundError as exc:
                raise errors.CompilerInternalError(
                    f"Lexer tables missing at {path}. Execute 'scriptum build-lexer' to generate them."
                ) from exc
            cls._TABLES_CACHE = cls._parse_tables(data)
        return cls._TABLES_CACHE

    @staticmethod
    def tables_path() -> Path:
        return Path(__file__).with_name("tables.json")

    @staticmethod
    def _parse_tables(data: dict) -> LexerTables:
        states_payload: list[DFAState] = []
        trans = data.get("trans", {})
        finals = {str(state) for state in data.get("finals", [])}
        labels = data.get("final_token_labels", {})
        priorities = data.get("final_token_priority", {})
        ignores = data.get("final_token_ignore", {})
        kinds = data.get("final_token_kind", {})
        indices = data.get("final_token_index", {})

        for state in data.get("states", []):
            state_key = str(state)
            transitions: dict[int, int] = {}
            for symbol, target in trans.get(state_key, {}).items():
                transitions[_symbol_to_code(symbol)] = int(target)

            accepting = None
            if state_key in finals:
                kind_name = kinds.get(state_key, "IDENTIFIER")
                try:
                    kind = tokens.TokenKind[kind_name]
                except KeyError:
                    kind = tokens.TokenKind.IDENTIFIER
                accepting = AcceptEntry(
                    index=int(indices.get(state_key, 0)),
                    name=labels.get(state_key, ""),
                    kind=kind,
                    priority=int(priorities.get(state_key, 0)),
                    ignore=bool(ignores.get(state_key, False)),
                )

            states_payload.append(DFAState(transitions=transitions, accepting=accepting))

        return LexerTables(start_state=int(data.get("start", 0)), states=states_payload)


def _symbol_to_code(symbol: str) -> int:
    if symbol.startswith("\\x") and len(symbol) == 4:
        return int(symbol[2:], 16)
    if symbol:
        return ord(symbol[0])
    raise ValueError("Invalid symbol representation in DFA table.")

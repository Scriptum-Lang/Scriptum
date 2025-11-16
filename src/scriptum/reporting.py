from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .text import Span, highlight_span, line_col


@dataclass(slots=True)
class ErrorReport:
    code: str
    message: str
    path: Optional[str] = None
    span: Optional[Span] = None
    source: Optional[str] = None

    def to_dict(self) -> dict:
        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.path:
            payload["path"] = self.path
        if self.span:
            payload["span"] = [self.span.start, self.span.end]
        if self.source and self.span:
            line, column = line_col(self.source, self.span)
            payload["position"] = {"line": line, "column": column}
            payload["highlight"] = highlight_span(self.source, self.span)
        return payload

    def format_cli_text(self) -> str:
        lines = [f"ERRO [{self.code}] {self.message}"]
        if self.path:
            if self.source and self.span:
                line, column = line_col(self.source, self.span)
                lines.append(f"--> {self.path}:{line}:{column}")
            else:
                lines.append(f"--> {self.path}")
        if self.source and self.span:
            snippet = highlight_span(self.source, self.span)
            for raw in snippet.splitlines():
                lines.append(f"    {raw}")
        return "\n".join(lines)

"""
Implementa o algoritmo de construção de subconjuntos (AFN→AFD) e minimização de Hopcroft
como ponto oficial da disciplina. Este módulo delega para o pipeline interno de regex/builder.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from ..regex.builder import build_tables_from_specs


def build_dfa_from_specs(
    specs: Iterable[Tuple[str, str, int] | Tuple[str, str, int, bool] | Tuple[str, str, int, bool, str]],
    *,
    deterministic_order: bool = True,
) -> Dict[str, Any]:
    """
    Constrói o AFD mínimo a partir de especificações de tokens via ER.

    Parameters
    ----------
    specs:
        Iterable de tuplas (token_name, regex, priority[, ignore][, kind])
    deterministic_order:
        Garante IDs de estado determinísticos (útil para testes/mermaid)

    Returns
    -------
    dict
        Dicionário com {states, start, finals, alphabet, trans,
        final_token_labels, final_token_priority, final_token_ignore, final_token_kind}
    """

    return build_tables_from_specs(specs, deterministic_order=deterministic_order)

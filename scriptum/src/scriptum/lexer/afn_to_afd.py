"""
Implementa o algoritmo de construcao de subconjuntos (AFN->AFD) e a minimizacao de Hopcroft
como ponto oficial da disciplina. Este modulo expone a representacao baseada em conjuntos
alinhada com o pipeline interno de regex/builder.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from ..regex import nfa, parser
from ..regex.builder import AcceptInfo, build_tables_from_specs as _build_tables_from_specs
from ..regex.dfa import DFA, DFAState


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
        acrescido de `subset_dfa` para inspecao dos automatos baseados em conjuntos.
    """

    tables = _build_tables_from_specs(specs, deterministic_order=deterministic_order)
    tables["subset_dfa"] = _build_subset_automaton(specs)
    return tables


@dataclass(frozen=True)
class _SpecPattern:
    name: str
    pattern: str
    priority: int
    ignore: bool
    kind: str


def _normalize_specs(
    specs: Iterable[Tuple[str, str, int] | Tuple[str, str, int, bool] | Tuple[str, str, int, bool, str]],
) -> List[_SpecPattern]:
    normalized: List[_SpecPattern] = []
    for item in specs:
        if len(item) < 3:
            raise ValueError("Each specification must contain at least (name, regex, priority).")
        name, pattern, priority = item[:3]
        ignore = bool(item[3]) if len(item) >= 4 else False
        kind_value: Any = item[4] if len(item) >= 5 else "TOKEN"
        kind = kind_value.name if hasattr(kind_value, "name") else str(kind_value)
        normalized.append(
            _SpecPattern(
                name=str(name),
                pattern=str(pattern),
                priority=int(priority),
                ignore=ignore,
                kind=kind,
            )
        )
    return normalized


def _build_subset_automaton(
    specs: Iterable[Tuple[str, str, int] | Tuple[str, str, int, bool] | Tuple[str, str, int, bool, str]],
) -> Dict[str, Any]:
    patterns = _normalize_specs(specs)
    regex_parser = parser.RegexParser(nfa.ASCII_LIMIT)
    thompson = nfa.ThompsonBuilder(nfa.ASCII_LIMIT)

    for index, pattern in enumerate(patterns):
        node = regex_parser.parse(pattern.pattern)
        info = AcceptInfo(
            index=index,
            name=pattern.name,
            kind=pattern.kind,
            priority=pattern.priority,
            ignore=pattern.ignore,
            order=index,
        )
        thompson.add_pattern(node, info)

    machine = thompson.to_nfa()
    dfa_machine, subsets = _determinize_with_subsets(machine)

    alphabet = [_symbol_to_str(code) for code in sorted(thompson.alphabet)]
    finals: List[int] = []
    states_payload: List[Dict[str, Any]] = []

    for state_id, state in enumerate(dfa_machine.states):
        subset = sorted(subsets.get(state_id, frozenset()))
        grouped = _group_transitions_by_target(state.transitions)
        transitions_payload = [
            {"target": target, "symbols": [_symbol_to_str(code) for code in sorted(symbols)]}
            for target, symbols in grouped
        ]

        accepting = None
        if state.accepting is not None:
            accepting = _accept_info_to_dict(state.accepting)
            finals.append(state_id)

        states_payload.append(
            {
                "id": state_id,
                "subset": subset,
                "transitions": transitions_payload,
                "accepting": accepting,
            }
        )

    return {
        "start": dfa_machine.start_state,
        "alphabet": alphabet,
        "states": states_payload,
        "finals": finals,
    }


def _determinize_with_subsets(machine: nfa.NFA) -> Tuple[DFA, Dict[int, frozenset[int]]]:
    start_closure = frozenset(machine.epsilon_closure({machine.start_state}))
    queue: deque[frozenset[int]] = deque([start_closure])
    subset_to_id: Dict[frozenset[int], int] = {start_closure: 0}
    id_to_subset: Dict[int, frozenset[int]] = {0: start_closure}
    states: List[DFAState] = [DFAState(accepting=_select_accepting(machine, start_closure))]

    while queue:
        current_subset = queue.popleft()
        current_id = subset_to_id[current_subset]
        transitions: Dict[int, Set[int]] = {}

        for state_id in current_subset:
            state = machine.states[state_id]
            for symbol, targets in state.transitions.items():
                transitions.setdefault(symbol, set()).update(targets)

        for symbol, targets in transitions.items():
            closure = frozenset(machine.epsilon_closure(targets))
            if not closure:
                continue
            if closure not in subset_to_id:
                new_id = len(states)
                subset_to_id[closure] = new_id
                id_to_subset[new_id] = closure
                states.append(DFAState(accepting=_select_accepting(machine, closure)))
                queue.append(closure)
            states[current_id].transitions[symbol] = subset_to_id[closure]

    return DFA(states=states, start_state=0), id_to_subset


def _group_transitions_by_target(transitions: Dict[int, int]) -> List[Tuple[int, Set[int]]]:
    grouped: Dict[int, Set[int]] = {}
    for symbol, target in transitions.items():
        grouped.setdefault(target, set()).add(symbol)
    return sorted(grouped.items(), key=lambda item: item[0])


def _accept_info_to_dict(info: AcceptInfo) -> Dict[str, Any]:
    return {
        "index": info.index,
        "name": info.name,
        "kind": info.kind,
        "priority": info.priority,
        "ignore": info.ignore,
    }


def _symbol_to_str(code: int) -> str:
    char = chr(code)
    if char.isprintable() or char in {"\n", "\t", " "}:
        return char
    return f"\\x{code:02x}"


def _select_accepting(machine: nfa.NFA, subset: Iterable[int]) -> Optional[Any]:
    best: Optional[Any] = None
    best_priority: Optional[int] = None
    best_order: Optional[int] = None

    for state_id in subset:
        payload = machine.accepting.get(state_id)
        if payload is None:
            continue
        priority = getattr(payload, "priority", None)
        order = getattr(payload, "order", None)
        if priority is None or order is None:
            continue
        if best is None:
            best = payload
            best_priority = priority
            best_order = order
            continue
        if priority > best_priority:
            best = payload
            best_priority = priority
            best_order = order
        elif priority == best_priority and order < best_order:
            best = payload
            best_order = order
    return best


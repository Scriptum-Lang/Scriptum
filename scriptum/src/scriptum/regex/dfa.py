"""
Deterministic finite automata generated from Scriptum regex NFAs.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from . import nfa

StateId = int


@dataclass(slots=True)
class DFAState:
    """Single deterministic state."""

    transitions: Dict[int, StateId] = field(default_factory=dict)
    accepting: Optional[Any] = None


@dataclass(slots=True)
class DFA:
    """Deterministic automaton used by the lexer."""

    states: List[DFAState]
    start_state: StateId

    # Utilities -----------------------------------------------------------------

    def alphabet(self) -> Set[int]:
        symbols: Set[int] = set()
        for state in self.states:
            symbols.update(state.transitions.keys())
        return symbols

    def make_total(self) -> None:
        """Ensure the DFA has total transitions by adding a sink state if necessary."""

        alphabet = sorted(self.alphabet())
        sink_state: Optional[int] = None

        def ensure_sink() -> int:
            nonlocal sink_state
            if sink_state is None:
                sink_state = len(self.states)
                sink = DFAState()
                self.states.append(sink)
            return sink_state

        for state in self.states:
            for symbol in alphabet:
                if symbol not in state.transitions:
                    sink = ensure_sink()
                    state.transitions[symbol] = sink

        if sink_state is not None:
            sink = self.states[sink_state]
            for symbol in alphabet:
                sink.transitions[symbol] = sink_state

    def minimize(self) -> "DFA":
        """Return a minimized copy of this DFA using Hopcroft's algorithm."""

        alphabet = sorted(self.alphabet())
        num_states = len(self.states)

        # Partition states by accepting payload.
        partitions: List[Set[int]] = []
        accept_groups: Dict[Any, Set[int]] = {}
        for state_id, state in enumerate(self.states):
            key = state.accepting
            accept_groups.setdefault(key, set()).add(state_id)
        partitions = [group for group in accept_groups.values()]

        worklist: deque[Set[int]] = deque(partitions)

        # Precompute predecessors for each symbol.
        predecessors: Dict[int, Dict[int, Set[int]]] = {
            symbol: {state_id: set() for state_id in range(num_states)} for symbol in alphabet
        }
        for src_id, state in enumerate(self.states):
            for symbol, dst_id in state.transitions.items():
                predecessors[symbol][dst_id].add(src_id)

        while worklist:
            splitter = worklist.popleft()
            for symbol in alphabet:
                involved: Set[int] = set()
                for state_id in splitter:
                    involved.update(predecessors[symbol][state_id])
                if not involved:
                    continue

                new_partitions: List[Set[int]] = []
                for block in partitions:
                    intersection = block & involved
                    difference = block - involved
                    if intersection and difference:
                        new_partitions.extend([intersection, difference])
                        if block in worklist:
                            worklist.remove(block)
                            worklist.extend([intersection, difference])
                        else:
                            if len(intersection) <= len(difference):
                                worklist.append(intersection)
                            else:
                                worklist.append(difference)
                    else:
                        new_partitions.append(block)
                partitions = new_partitions

        state_mapping: Dict[int, int] = {}
        minimized_states: List[DFAState] = []
        for new_id, block in enumerate(partitions):
            representative = next(iter(block))
            state_mapping.update({state: new_id for state in block})
            original_state = self.states[representative]
            minimized_state = DFAState(accepting=original_state.accepting)
            minimized_states.append(minimized_state)

        for old_id, state in enumerate(self.states):
            new_source = state_mapping[old_id]
            new_state = minimized_states[new_source]
            for symbol, target in state.transitions.items():
                new_state.transitions[symbol] = state_mapping[target]

        new_start = state_mapping[self.start_state]
        return DFA(states=minimized_states, start_state=new_start)


def determinize(machine: nfa.NFA) -> DFA:
    """Determinise *machine* via the subset construction."""

    start_closure = frozenset(machine.epsilon_closure({machine.start_state}))
    queue: deque[frozenset[int]] = deque([start_closure])
    subsets: Dict[frozenset[int], int] = {start_closure: 0}
    states: List[DFAState] = [DFAState(accepting=_select_accepting(machine, start_closure))]

    while queue:
        current_subset = queue.popleft()
        current_index = subsets[current_subset]
        transitions: Dict[int, Set[int]] = {}

        for state_id in current_subset:
            state = machine.states[state_id]
            for symbol, targets in state.transitions.items():
                transitions.setdefault(symbol, set()).update(targets)

        for symbol, targets in transitions.items():
            closure = frozenset(machine.epsilon_closure(targets))
            if not closure:
                continue
            if closure not in subsets:
                subsets[closure] = len(states)
                states.append(DFAState(accepting=_select_accepting(machine, closure)))
                queue.append(closure)
            states[current_index].transitions[symbol] = subsets[closure]

    return DFA(states=states, start_state=0)


def _select_accepting(machine: nfa.NFA, subset: Iterable[int]) -> Optional[Any]:
    best: Optional[Any] = None
    best_priority: Optional[int] = None
    best_order: Optional[int] = None

    for state_id in subset:
        payload = machine.accepting.get(state_id)
        if payload is None:
            continue
        priority, order = payload.priority, payload.order
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

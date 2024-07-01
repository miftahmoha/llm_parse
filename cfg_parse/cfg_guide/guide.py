import warnings
from collections import defaultdict, deque
from copy import deepcopy
from functools import wraps
from typing import Deque, Optional

from cfg_parse.base import (
    Symbol,
    SymbolGraph,
    SymbolGraphState,
    SymbolType,
)
from cfg_parse.cfg_build.build import build_symbol_graph
from cfg_parse.cfg_guide.helpers import (
    _push_stateful_symbol_graph_layer_to_stack,
    _divide_cfg_grammar_into_definitions,
    _exist_infinite_loop_around_non_terminal_symbols,
    _get_non_terminal_loop_str_from_generation_state_stack,
    _turn_symbol_graph_into_stateful_obj,
)

CFGGenerationState = Optional[Deque[SymbolGraphState]]


def build_cfg_grammar_into_symbol_graphs(cfg_grammar: str) -> dict[str, SymbolGraph]:
    built_cfg_grammar_dict: dict[str, SymbolGraph] = {}

    divided_cfg_grammar_dict = _divide_cfg_grammar_into_definitions(cfg_grammar)

    for symbol_name, symbol_def in divided_cfg_grammar_dict.items():
        built_cfg_grammar_dict[symbol_name] = build_symbol_graph(symbol_def)

    return built_cfg_grammar_dict


def get_next_terminals(
    built_cfg_grammar: dict[str, SymbolGraph],
    generation_state: CFGGenerationState = None,
    chosen_symbol: Optional[Symbol] = None,
):
    next_terminal_symbols_w_history: dict[Symbol, Deque[SymbolGraphState]] = (
        defaultdict(deque)
    )

    def recurse_guide(
        generation_state: CFGGenerationState = None,
        chosen_symbol: Optional[Symbol] = None,
    ):
        # Ignore paths where there are infinite loops of non-terminals.
        if generation_state is None:
            if chosen_symbol is None:
                start = _turn_symbol_graph_into_stateful_obj(
                    built_cfg_grammar["start"], "start"
                )
                recurse_guide(deque([start]))
                return
            else:
                raise ValueError(
                    "`CFGGenerationState` is None while `chosen_symbol` is not."
                )

        if _exist_infinite_loop_around_non_terminal_symbols(generation_state):
            warnings.warn(
                f"A loop of non-terminal symbols is found {_get_non_terminal_loop_str_from_generation_state_stack(deepcopy(generation_state))}, path will be ignored."
            )
            return

        if chosen_symbol is None:
            # Poping the last graph.
            last_visit_graph = generation_state[-1].graph
            # Poping the last state.
            last_visit_symbol = generation_state[-1].state
            # Get the next nodes according to `last_visit_symbol`, which refers to the last visited (non-terminal) symbol from where the stack was addded.
            next_symbols = (
                last_visit_graph.tree[last_visit_symbol]
                if last_visit_symbol is not None
                else last_visit_graph.initials
            )

            for next_symbol in next_symbols:
                if next_symbol.s_type in [
                    SymbolType.TERMINAL,
                    SymbolType.REGEX,
                    SymbolType.SPECIAL,
                ]:
                    next_terminal_symbols_w_history[next_symbol] = deepcopy(
                        generation_state
                    )

                # Create an additional layer in the stack.
                if next_symbol.s_type == SymbolType.NON_TERMINAL:
                    last_generation_state = _push_stateful_symbol_graph_layer_to_stack(
                        deepcopy(generation_state),
                        built_cfg_grammar[next_symbol.content],
                        next_symbol,
                    )
                    recurse_guide(last_generation_state)

            return

        if chosen_symbol.content == "EOS_SYMBOL":
            generation_state.pop()
            # Should return the last label, but as a symbol of the last symbol graph.
            recurse_guide(deepcopy(generation_state))
            return

        # Poping the last graph.
        last_visit_graph = generation_state[-1].graph
        # Get the next nodes according to `chosen_symbol`, which refers to the (terminal) symbol chosen by the LLM.
        next_symbols = last_visit_graph.tree[chosen_symbol]
        # Update the state for `SymbolGraphState` to the (terminal) symbol chosen by the LLM.
        generation_state[-1].state = chosen_symbol

        for next_symbol in next_symbols:
            if next_symbol.s_type in [
                SymbolType.TERMINAL,
                SymbolType.REGEX,
                SymbolType.SPECIAL,
            ]:
                next_terminal_symbols_w_history[next_symbol] = deepcopy(
                    generation_state  # type: ignore
                )

            # Create an additional layer in the stack.
            if next_symbol.s_type == SymbolType.NON_TERMINAL:
                generation_state = _push_stateful_symbol_graph_layer_to_stack(
                    deepcopy(generation_state),  # type: ignore
                    built_cfg_grammar[next_symbol.content],
                    next_symbol,
                )

    recurse_guide(generation_state, chosen_symbol)

    return next_terminal_symbols_w_history


def clear_dict_before_call(dict_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            getattr(self, dict_name).clear()
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class CFGGuide:
    built_cfg_grammar: dict[str, SymbolGraph]
    next_terminals_w_history: dict[Symbol, CFGGenerationState]

    def __init__(self, cfg_grammar: str):
        self.built_cfg_grammar = build_cfg_grammar_into_symbol_graphs(cfg_grammar)
        self.next_terminals_w_history = {}

    @clear_dict_before_call("next_terminals_w_history")
    def get_next_terminals(
        self,
        generation_state: CFGGenerationState = None,
        chosen_symbol: Optional[Symbol] = None,
    ):
        # Ignore paths where there are infinite loops of non-terminals.
        if generation_state is None:
            if chosen_symbol is None:
                start = _turn_symbol_graph_into_stateful_obj(
                    self.built_cfg_grammar["start"], "start"
                )
                self.get_next_terminals(generation_state=deque([start]))
                return
            else:
                raise ValueError(
                    "`CFGGenerationState` is `None` while `chosen_symbol` is not."
                )

        # [NOTE] This is way more complicated than it seems, this can loop X times then choose
        # another path. Should it be stopped? What about some `LIMIT_LOOP_NON_TERMINAL_DEFAULT`?
        if _exist_infinite_loop_around_non_terminal_symbols(generation_state):
            warnings.warn(
                f"A loop of non-terminal symbols is found {_get_non_terminal_loop_str_from_generation_state_stack(deepcopy(generation_state))}, path will be ignored."
            )
            return

        if chosen_symbol is None:
            # Poping the last graph.
            last_visit_graph = generation_state[-1].graph
            # Poping the last state.
            last_visit_symbol = generation_state[-1].state
            # Get the next nodes according to `last_visit_symbol`, which refers to the last visited (non-terminal) symbol from where the stack was addded.
            next_symbols = (
                last_visit_graph.tree[last_visit_symbol]
                if last_visit_symbol is not None
                else last_visit_graph.initials
            )

            # [NOTE] Sometimes `next_symbols` is returned empty, this can happen when:
            # (1) You pop from the stack, and the place where you land was a `END-OF-DEFINITON`
            # non-terminal symbol (we return a None chosen symbol after poping from the stack).
            # (2) The second case where we pass a `chosen_symbol = None` is at the beggining,
            # this would then happen if `start` is connected to one single terminal symbol.
            # Handles reaching the end of a symbol graph (`next_symbols` being empty).
            if not next_symbols:
                generation_state.pop()
                # Handles reaching the end of stack.
                if not generation_state:
                    return
                # Should return the last label, but as a symbol of the last symbol graph.
                self.get_next_terminals(deepcopy(generation_state))
                return

            for next_symbol in next_symbols:
                if next_symbol.s_type in [
                    SymbolType.TERMINAL,
                    SymbolType.REGEX,
                    SymbolType.SPECIAL,
                ]:
                    self.next_terminals_w_history[next_symbol] = deepcopy(
                        generation_state
                    )

                # Create an additional layer in the stack.
                if next_symbol.s_type == SymbolType.NON_TERMINAL:
                    last_generation_state = _push_stateful_symbol_graph_layer_to_stack(
                        deepcopy(generation_state),
                        self.built_cfg_grammar[next_symbol.content],
                        next_symbol,
                    )
                    self.get_next_terminals(last_generation_state)

            return

        # Poping the last graph.
        last_visit_graph = generation_state[-1].graph

        # Get the next nodes according to `chosen_symbol`, which refers to the (terminal) symbol chosen by the LLM.
        next_symbols = last_visit_graph.tree[chosen_symbol]

        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        if not next_symbols:
            generation_state.pop()
            # Handles reaching the end of stack.
            if not generation_state:
                return
            # Should return the last label, but as a symbol of the last symbol graph.
            self.get_next_terminals(deepcopy(generation_state))
            return

        # Update the state for `SymbolGraphState` to the (terminal) symbol chosen by the LLM.
        generation_state[-1].state = chosen_symbol

        # [NOTE] Do something about this?
        for next_symbol in next_symbols:
            if next_symbol.s_type in [
                SymbolType.TERMINAL,
                SymbolType.REGEX,
                SymbolType.SPECIAL,
            ]:
                self.next_terminals_w_history[next_symbol] = deepcopy(generation_state)

            # Create an additional layer in the stack.
            if next_symbol.s_type == SymbolType.NON_TERMINAL:
                self.get_next_terminals(
                    _push_stateful_symbol_graph_layer_to_stack(
                        deepcopy(generation_state),  # type: ignore
                        self.built_cfg_grammar[next_symbol.content],
                        next_symbol,
                    )
                )

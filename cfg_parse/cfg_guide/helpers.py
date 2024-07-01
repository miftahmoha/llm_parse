import warnings
import random
import re

from typing import Deque

from cfg_parse.base import Symbol, SymbolGraph, SymbolGraphState, SymbolType
from cfg_parse.exceptions import InvalidGrammar, ParsingError


def _divide_cfg_grammar_into_definitions(grammar: str) -> dict[str, str]:
    divided_cfg_grammar_dict: dict[str, str] = {}
    current_rule: str = ""

    lines = grammar.strip().split("\n")

    for line in lines:
        line = line.strip()

        if not line:
            # Skip empty lines.
            continue

        if ":" not in line:
            if not current_rule:
                raise InvalidGrammar(f"Missing `:` in '''{line}'''")

            divided_cfg_grammar_dict[current_rule] += " " + line

        else:
            parts = line.split(":")

            if len(parts) != 2:
                # Handles multiple use of ':' in a single definition.
                raise InvalidGrammar(f"Invalid grammar rule: {line}")

            current_rule, definition = parts

            if current_rule in divided_cfg_grammar_dict:
                raise InvalidGrammar(f"Redefinition of grammar rule: {line}")

            divided_cfg_grammar_dict[current_rule] = definition.strip()

    if "start" not in divided_cfg_grammar_dict:
        raise InvalidGrammar(f"The symbol `start` is non-existant.")

    return divided_cfg_grammar_dict


# [NOTE] `StatefulSymbolGraph` is better.
def _turn_symbol_graph_into_stateful_obj(symbol_graph: SymbolGraph, label: str):
    return SymbolGraphState(symbol_graph, label)


def _push_stateful_symbol_graph_layer_to_stack(
    generation_state: Deque[SymbolGraphState],
    symbol_graph_state_symbol_graph: SymbolGraph,
    symbol_graph_state_symbol: Symbol,
):
    symbol_graph_state_upper_layer = _turn_symbol_graph_into_stateful_obj(
        symbol_graph_state_symbol_graph, symbol_graph_state_symbol.content
    )

    # Set up the state for the bottom stack layer, it'll save where we left for when
    # we pop the upper stack layer. We would then search for the next symbols from
    # the last non-terminal symbol.
    generation_state[-1].state = symbol_graph_state_symbol

    # Add stack layer `StackGraphState` to `Deque[SymbolGraphState]`.
    generation_state.append(symbol_graph_state_upper_layer)

    return generation_state


def _get_non_terminal_loop_str_from_generation_state_stack(
    generation_state_loop_queue: Deque[SymbolGraphState],
) -> str:
    initial = generation_state_loop_queue.popleft()

    result = initial.label

    for generation_state in generation_state_loop_queue:
        result += " ->" + generation_state.label

    result += " ->" + initial.label

    return result


def _exist_infinite_loop_around_non_terminal_symbols(
    generation_state: Deque[SymbolGraphState],
) -> bool:
    if len(generation_state) > 1:
        return generation_state[-1].label == generation_state[0].label
    return False


def _extract_str_from_symbols(symbols: list[Symbol]) -> list[str]:
    symbols_str: list[str] = []
    for symbol in symbols:
        symbols_str.append(symbol.content)
    return symbols_str


def _get_next_terminal_symbols_as_regex(
    symbols: list[Symbol],
) -> str:
    regexes: list[str] = []

    for symbol in symbols:
        if symbol.s_type == SymbolType.TERMINAL:
            regexes.append(re.escape(symbol.content))
        elif symbol.s_type == SymbolType.REGEX:
            regexes.append(symbol.content)
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    return r"(" + r"|".join([r"(" + x + r")" for x in regexes]) + r")"


def _validate_regex(string: str, pattern: str) -> bool:
    regex = re.compile(pattern)
    if regex.fullmatch(string):
        return True
    return False


def _retrace_symbol_obj_from_str(
    chosen_symbol_str: str,
    next_terminal_symbols: list[Symbol],
) -> Symbol:
    chosen_symbols: list[Symbol] = []

    for symbol in next_terminal_symbols:
        # [NOTE] `chosen_symbol_str` could represent more than one symbol in different paths. Send a warning and randomly pick a symbol with equal probability.
        if symbol.s_type == SymbolType.REGEX:
            if _validate_regex(chosen_symbol_str, symbol.content):
                chosen_symbols.append(symbol)
        elif symbol.s_type == SymbolType.TERMINAL:
            if symbol.content == chosen_symbol_str:
                chosen_symbols.append(symbol)
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    # [NOTE] Could be interactive here.
    # Shows the different paths and lets the user choose which one.
    if len(chosen_symbols) > 2:
        warnings.warn(
            "Chosen symbol present in multiple paths, one will be picked with equal probability."
        )
        chosen_symbol = random.choice(chosen_symbols)
        return chosen_symbol

    return chosen_symbols[0]

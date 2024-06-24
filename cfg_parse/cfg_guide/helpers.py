from typing import Deque

from cfg_parse.base import Symbol, SymbolGraph, SymbolGraphState
from cfg_parse.exceptions import InvalidGrammar


def _divide_cfg_grammar_into_definitions(
    grammar: str, start: str = "start"
) -> dict[str, str]:
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

    # Sets the chosen start.
    if start in divided_cfg_grammar_dict:
        divided_cfg_grammar_dict["start"] = divided_cfg_grammar_dict[start]
        if start != "start":
            del divided_cfg_grammar_dict[start]
    else:
        raise InvalidGrammar(f"The symbol {start} is non-existant.")

    return divided_cfg_grammar_dict


def _turn_symbol_graph_into_stateful_obj(symbol_graph: SymbolGraph, label: str):
    return SymbolGraphState(symbol_graph, label)


def _add_stateful_symbol_graph_layer_to_generation_state_stack(
    generation_state: Deque[SymbolGraphState],
    symbol_graph_state_symbol_graph: SymbolGraph,
    symbol_graph_state_symbol: Symbol,
):
    symbol_graph_state_upper_layer = _turn_symbol_graph_into_stateful_obj(
        symbol_graph_state_symbol_graph, symbol_graph_state_symbol.content
    )

    # Set up the state for the bottom stack layer, it'll save where we left for when
    # we pop the upper stack layer. We would then search for the next symbols from
    # the saved state.
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

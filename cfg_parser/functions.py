from collections import defaultdict, deque
from copy import deepcopy

from typing import Deque
from cfg_parser.base import Symbol, SymbolType, OrderedSet
from cfg_parser.exceptions import SymbolNotFound


def convert_str_to_symbol(symbol_str: str) -> Symbol:
    if symbol_str.startswith('"') and symbol_str.endswith('"'):
        node = Symbol(symbol_str, SymbolType.TERMINAL)

    elif symbol_str.startswith("Regex(") and symbol_str.endswith(")"):
        # Index to strip `symbol` from `Regex()`.
        start = symbol_str.find("(")

        node = Symbol(symbol_str[start + 1 : -1], SymbolType.REGEX)

    elif symbol_str in ("(", ")", "[", "]", "{", "}"):
        node = Symbol(symbol_str, SymbolType.SPECIAL)

    else:
        node = Symbol(symbol_str, SymbolType.NOT_TERMINAL)

    return node


def find_symbol_antecedent(
    symbol_graph: dict[Symbol, OrderedSet[Symbol]], search_symbol: Symbol
):
    for symbol_parent, symbol_children in symbol_graph.items():
        if search_symbol in symbol_children:
            return symbol_parent

    raise SymbolNotFound(f"Symbol was not found.")


# [TODO] Needs to be fixed.
def get_special_symbol(
    symbol_graph: dict[Symbol, OrderedSet[Symbol]], symbol_str: str
) -> Symbol:
    for symbol in symbol_graph:
        if symbol.content == symbol_str:
            return symbol

    return Symbol("ERROR", SymbolType.SPECIAL)


def check_definition(symbol_def: str):
    # [TODO] Throws the corresponding exceptions.
    pass


# [TODO] Need additional ( ) at the beggining for `build_full_graph` to work.
def insert_standard_delimiters(symbol_def: str):
    return "(" + symbol_def + ")"


def insert_space_between_delimiters(s):
    in_quote = False
    in_regex = False
    result = []
    i = 0

    while i < len(s):
        if s[i] == '"':
            in_quote = not in_quote
            result.append(s[i])
        elif s[i : i + 5] == "Regex":
            in_regex = True
            result.append(s[i])
        elif s[i] in "([{" and not in_quote and not in_regex:
            result.append(" " + s[i] + " ")
        elif s[i] in ")]}" and not in_quote and not in_regex:
            result.append(" " + s[i] + " ")
        elif s[i] == ")" and in_regex:
            in_regex = False
            result.append(s[i])
        else:
            result.append(s[i])
        i += 1

    return "".join(result)


def pre_process_symbol_def(symbol_def: str):
    return insert_space_between_delimiters(insert_standard_delimiters(symbol_def))


def convert_str_def_to_str_queue(symbol_def: str) -> Deque[str]:
    check_definition(symbol_def)

    pre_processed_symbol_def = pre_process_symbol_def(symbol_def)
    symbols = pre_processed_symbol_def.split()

    queue = deque()
    for symbol in symbols:
        queue.append(symbol)

    return queue


def get_symbols_from_generated_symbol_graph(
    generated_symbol_graph: dict[Symbol, OrderedSet[Symbol]]
) -> dict[str, Symbol]:
    start = generated_symbol_graph[get_special_symbol(generated_symbol_graph, "SOURCE")]
    visited = dfs(deepcopy(generated_symbol_graph), start)

    # The reason '"-"' is swapped is because the second one is in the keys.
    symbols: dict[str, Symbol] = {}
    # The default int is OrderedSet to 0.
    order: dict[str, int] = defaultdict(int)
    for symbol in visited:
        symbols[symbol.content + f"|{order[symbol.content]}"] = symbol
        order[symbol.content] += 1

    # Adding the SOURCE and the SINK
    symbols["SOURCE"] = get_special_symbol(generated_symbol_graph, "SOURCE")
    symbols["SINK"] = get_special_symbol(generated_symbol_graph, "SINK")

    return symbols


# A `queue` instad of a `stack`, just a convenience for testing.
def dfs(
    symbol_graph: dict[Symbol, OrderedSet[Symbol]], start: OrderedSet[Symbol]
) -> list[Symbol]:
    visited = []
    queue = deque()  # type: ignore
    queue.extend(list(start))
    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph[vertex])
    return visited

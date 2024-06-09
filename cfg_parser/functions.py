from collections import defaultdict, deque
from copy import deepcopy
from typing import Deque

from cfg_parser.base import Symbol, SymbolType, SymbolGraph, OrderedSet
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


def get_symbol_antecedent(
    symbol_graph_nodes: dict[Symbol, OrderedSet[Symbol]], search_symbol: Symbol
) -> Symbol:
    for symbol_parent, symbol_children in symbol_graph_nodes.items():
        if search_symbol in symbol_children:
            return symbol_parent

    raise SymbolNotFound(f"Symbol {search_symbol.content} was not found.")


def get_symbol_antecedents(
    symbol_graph_nodes: dict[Symbol, OrderedSet[Symbol]], search_symbol: Symbol
) -> Symbol:
    symbol_antecedents = []
    for symbol_parent, symbol_children in symbol_graph_nodes.items():
        if search_symbol in symbol_children:
            symbol_antecedents.append(symbol_parent)

    if len(symbol_antecedents) == 0:
        raise SymbolNotFound(
            f"No Symbol antecedent for {search_symbol.content} was found."
        )

    return symbol_antecedents


def is_contain_eos_token(symbol_graph_nodes: dict[Symbol, OrderedSet[Symbol]]) -> bool:
    for symbol in symbol_graph_nodes:
        if symbol.content == "EOS_TOKEN" and symbol.s_type == SymbolType.SPECIAL:
            return True
    return False


def discard_single_nodes(
    symbol_graph_nodes: dict[Symbol, OrderedSet[Symbol]]
) -> SymbolGraph:
    single_node_symbols = []
    symbol_graph_nodes_copy = symbol_graph_nodes.copy()

    for symbol_key in symbol_graph_nodes_copy.keys():
        if not symbol_graph_nodes_copy[symbol_key]:
            single_node_symbols.append(symbol_key)

    for single_node_symbol in single_node_symbols:
        del symbol_graph_nodes_copy[single_node_symbol]

    return symbol_graph_nodes_copy


def get_symbols_with_content(
    symbol_graph: OrderedSet[Symbol], content: str
) -> list[Symbol]:
    symbols = []
    for symbol in symbol_graph:
        if symbol.content == content:
            symbols.append(symbol)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No Symbol matching {content} was found.")

    return symbols


def check_for_errors(symbol_def: str):
    # [TODO] Throws the corresponding exceptions.
    pass


# [TODO] Need additional initial `( )` for `build_full_graph` to start.
def insert_standard_delimiters(symbol_def: str):
    return "(" + symbol_def + ")"


# Insert space between delimiters, `terminal` delimiters `"(", ")", "[", "]", "{", "}"` are not considered.
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
    pre_processed_symbol_def = pre_process_symbol_def(symbol_def)
    symbols = pre_processed_symbol_def.split()

    queue = deque()
    for symbol in symbols:
        queue.append(symbol)

    return queue


def get_symbols_from_generated_symbol_graph(
    symbol_graph: SymbolGraph,
) -> dict[str, Symbol]:
    symbols: dict[str, Symbol] = {}

    start = symbol_graph.initials
    visited = new_dfs(symbol_graph.copy(), start)

    # The default int is OrderedSet to 0.
    order: dict[str, int] = defaultdict(int)
    for symbol in visited:
        symbols[symbol.content + f"|{order[symbol.content]}"] = symbol
        order[symbol.content] += 1

    return symbols


def new_dfs(symbol_graph: SymbolGraph, start: OrderedSet[Symbol]) -> list[Symbol]:
    visited = []

    queue = deque()  # type: ignore
    queue.extend(list(start))

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.nodes[vertex])

    return visited

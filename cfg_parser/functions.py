from collections import defaultdict, deque
from typing import Deque
import re

from cfg_parser.base import Symbol, SymbolType, SymbolGraph, OrderedSet
from cfg_parser.exceptions import SymbolNotFound, InvalidSymbol, InvalidDelimiters, InvalidGrammar


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


def get_symbol_antecedents(
    symbol_graph_nodes: dict[Symbol, OrderedSet[Symbol]], search_symbol: Symbol
) -> list[Symbol]:
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
) -> dict[Symbol, OrderedSet[Symbol]]:
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

# Does every opening delimiter have an enclosing one?
def check_for_delimiter_coherence(symbol_def_str: list[str]):
    stack_delim_tracker = deque()

    # A standard delimiter is always added at the beggining.
    stack_delim_tracker.append('(')

    # [TODO] Throws the corresponding exceptions.
    for symbol_str in symbol_def_str:
        if symbol_str == '(':
            stack_delim_tracker.append(symbol_str)

        elif symbol_str == ')':
            if stack_delim_tracker[-1] != '(':
                raise InvalidDelimiters(f'Non enclosed delimiter {"("} in {"".join(stack_delim_tracker)}')
            stack_delim_tracker.pop()

        elif symbol_str == '{':
            stack_delim_tracker.append(symbol_str)
            
        elif symbol_str == '}':
            if stack_delim_tracker[-1] != '{':
                raise InvalidDelimiters(f'Non enclosed delimiter {"{"} in {"".join(stack_delim_tracker)}')
            stack_delim_tracker.pop()

        elif symbol_str == '[':
            stack_delim_tracker.append(symbol_str)

        elif symbol_str == ']':
            if stack_delim_tracker[-1] != '[':
                raise InvalidDelimiters(f'Non enclosed delimiter {"["} in {"".join(stack_delim_tracker)}')

            stack_delim_tracker.pop()


# Are symbols syntatically correct? 
def check_syntactic_soundness_symbols(symbol_def_str: list[str]):
    def xor(condition_lhs: bool, condition_rhs: bool):
        return bool(condition_lhs) ^ bool(condition_rhs)

    def is_terminal(symbol_str: str):
        return symbol_str[0] == '"' and symbol_str[-1] == '"'

    # [NOTE] `EOS_TOKEN` is a special symbol, turn it into a terminal?
    def is_special_symbol(symbol_str: str):
        return len(symbol_str) == 1

    def is_regex_symbol(symbol_str: str):
        return symbol_str.startswith("Regex(") and symbol_str.endswith(")")

    # Special characters REGEX.
    regex = re.compile(r'[@_!#$%^&*()<>?/\\|}~:]')

    for symbol_str in symbol_def_str:
        # 1) Are terminal symbols enclosed with `"` or without? `"symbol` or `symbol"` shouldn't be allowed.
        if xor(symbol_str[0] == '"', symbol_str[-1] == '"'):
            raise InvalidSymbol(f'Invalid symbol name {symbol_str}, symbols can be either `symbol_str` for non-terminal symbols or `"symbol_str" for terminal symbols.')
        
        # 2) Special characters shouldn't be allowed as symbol names for non terminals.
        if (not is_terminal(symbol_str)) and (not is_special_symbol(symbol_str)) and (not is_regex_symbol(symbol_str)) and (regex.search(symbol_str) != None):
            raise InvalidSymbol(f'Invalid symbol name {symbol_str}, special characters are not allowed')


# This should check if the definition is correct.
def check_for_errors(symbol_def_str: list[str]):
    # [NOTE] Needs tests.
    check_for_delimiter_coherence(symbol_def_str)
    check_syntactic_soundness_symbols(symbol_def_str)


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


def pre_process_symbol_def(symbol_def: str) -> str:
    return insert_space_between_delimiters(insert_standard_delimiters(symbol_def))


def convert_str_def_to_str_queue(symbol_def: str) -> Deque[str]:
    pre_processed_symbol_def = pre_process_symbol_def(symbol_def)
    symbols = pre_processed_symbol_def.split()

    # Check for errors.
    check_for_errors(symbols)

    queue = deque()
    for symbol in symbols:
        queue.append(symbol)

    return queue


def get_symbols_from_generated_symbol_graph(
    symbol_graph: SymbolGraph,
) -> dict[str, Symbol]:
    symbols: dict[str, Symbol] = {}

    start = symbol_graph.initials
    visited = dfs(symbol_graph.copy(), start)

    # The default int is OrderedSet to 0.
    order: dict[str, int] = defaultdict(int)
    for symbol in visited:
        symbols[symbol.content + f"|{order[symbol.content]}"] = symbol
        order[symbol.content] += 1

    return symbols


def dfs(symbol_graph: SymbolGraph, start: OrderedSet[Symbol]) -> list[Symbol]:
    visited = []

    queue = deque()  # type: ignore
    queue.extend(list(start))

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.nodes[vertex])

    return visited

from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

class SymbolType(Enum):
    TERMINAL = 1
    NOT_TERMINAL = 2
    REGEX = 3


@dataclass
class Symbol:
    content: str
    s_type: SymbolType

    def __hash__(self):
        return hash((self.content, self.s_type))

    def __eq__(self, other):
        # Ensure equality is checked for all fields
        if not isinstance(other, Symbol):
            return False

        return self.content == other.content and self.s_type == other.s_type

def convert_str_to_Symbol(symbol_str: str) -> Symbol:
    if symbol_str.startswith('"') and symbol_str.endswith('"'):
        node = Symbol(symbol_str, SymbolType.TERMINAL)

    elif symbol_str.startswith("Regex(") and symbol_str.endswith(")"):
        # Index to strip `symbol` from `Regex()`.
        start = symbol_str.find('(') 

        node = Symbol(symbol_str[start+1:-1], SymbolType.REGEX)

    else:
        node = Symbol(symbol_str, SymbolType.NOT_TERMINAL)
    
    return node


def construct_symbol_graph(definition: str):
    # (1) Separates strings, separator is ` `.
    # (2) Should be executed in a nested manner, between each ().

    symbols = definition.split()

    symbol_graph = defaultdict(set)

    # Useful in connecting graphs, trading a little bit of memory for speed.
    symbol_source = Symbol('SOURCE', SymbolType.NOT_TERMINAL)
    symbol_sink = Symbol('SINK', SymbolType.NOT_TERMINAL)

    symbol_previous = symbol_source
    for symbol_str in symbols:

        if symbol_str == '|':
            symbol_graph[symbol_sink].add(symbol_previous)
            symbol_previous = symbol_source
            continue
        
        node = convert_str_to_Symbol(symbol_str)

        symbol_graph[symbol_previous].add(node)
        
        # elif symbol.startswith('"') and symbol.endswith('"'):
        #     node = Symbol(symbol, SymbolType.TERMINAL)
        #     symbol_graph[symbol_previous].add(node)

        # elif symbol.startswith("Regex(") and symbol.endswith(")"):
        #     # Index to strip `symbol` from `Regex()`.
        #     start = symbol.find('(') 

        #     node = Symbol(symbol[start+1:-1], SymbolType.REGEX)
        #     symbol_graph[symbol_previous].add(node)

        # else:
        #     node = Symbol(symbol, SymbolType.NOT_TERMINAL)
        #     symbol_graph[symbol_previous].add(node)

        symbol_previous = node
    
    # Adding the last node to the sink.
    symbol_graph[symbol_sink].add(convert_str_to_Symbol(symbols[-1])) 

    return symbol_graph

def merge_dicts(symbol_graph_sink: dict[Symbol, set[Symbol]], symbol_graph_source: dict[Symbol, set[Symbol]]) -> dict[Symbol, set[Symbol]]:
    merged_dict = defaultdict(set)
    for key in symbol_graph_sink.keys() | symbol_graph_source.keys():
        merged_dict[key] = symbol_graph_sink[key] | symbol_graph_source[key]
    return merged_dict

# [SUGGESTION] Add a parameter that takes '()', '[]' or '{}' and build the logic accordingly.
# Or perhaps have a different function for each case.

# [IMPORTANT] It seems like the logic for [] will be expressed in the connection utility, [] is similar to a standard connection.
# The difference resides in the node `N` connected to the [] graph, it should have an option to go to `EOS_TOKEN` node 
# (if `N` has no other connection than the [] graph). EDIT: Same for {}. 

# [TODO] Need a utility that'll connect symbol_graphs `GRAPH_1` and `GRAPH_2` in ([GRAPH_1]() [GRAPH_2]()),
# the notion of connection will be discussed later.
# [TODO] Logic for {} and [] in EBF.

def connect_symbol_graph(symbol_graph_sink: dict[Symbol, set[Symbol]], symbol_graph_source: dict[Symbol, set[Symbol]]) -> dict[Symbol, set[Symbol]]:
    # [CAUTION] There could be common elements in the SOURCE and SINK.
    # symbol_graph_output = defaultdict(set)
    
    symbol_source = Symbol('SOURCE', SymbolType.NOT_TERMINAL)
    symbol_sink = Symbol('SINK', SymbolType.NOT_TERMINAL)

    source = symbol_graph_source[symbol_source]
    symbol_graph_source.pop(symbol_source)

    sink = symbol_graph_sink[symbol_sink]
    symbol_graph_sink.pop(symbol_sink)

    symbol_graph_output = merge_dicts(symbol_graph_sink, symbol_graph_source)
    
    for symbol_sink_elem in sink:
        for symbol_source_elem in source:
            # Avoids duplicates, (SINK) -> set{(1), (2)}; (SOURCE) -> set{(1), (?)} >>>>>> AVOIDS (1) -> (1).
            if symbol_sink_elem == symbol_source_elem:
                continue

            symbol_graph_output[symbol_sink_elem].add(symbol_source_elem)

    return symbol_graph_output

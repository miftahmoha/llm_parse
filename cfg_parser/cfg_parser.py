import uuid

from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
from typing import Deque

class SymbolType(Enum):
    TERMINAL = 1
    NOT_TERMINAL = 2
    REGEX = 3
    SPECIAL = 4

class SymbolGraphType(Enum):
    STANDARD = 1
    NONE_ANY = 2
    NONE_ONCE = 3

@dataclass
class Symbol:
    content: str
    s_type: SymbolType
    s_id: uuid.UUID = uuid.uuid4()

    def __hash__(self):
        return hash((self.content, self.s_type, self.s_id))

    def __eq__(self, other):
        # Ensure equality is checked for all fields
        if not isinstance(other, Symbol):
            return False

        return (self.content == other.content) and (self.s_type == other.s_type) and (self.s_id == other.s_id)

def convert_str_to_Symbol(symbol_str: str) -> Symbol:
    if symbol_str.startswith('"') and symbol_str.endswith('"'):
        node = Symbol(symbol_str, SymbolType.TERMINAL)

    elif symbol_str.startswith("Regex(") and symbol_str.endswith(")"):
        # Index to strip `symbol` from `Regex()`.
        start = symbol_str.find('(') 

        node = Symbol(symbol_str[start+1:-1], SymbolType.REGEX)

    elif symbol_str in ('(', ')', '[', ']', '{', '}'):
        node = Symbol(symbol_str, SymbolType.SPECIAL)

    else:
        node = Symbol(symbol_str, SymbolType.NOT_TERMINAL)
    
    return node


def construct_symbol_graph(definition: str, graph_type: SymbolGraphType = SymbolGraphType.STANDARD) -> dict[Symbol, set[Symbol]]:
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

        symbol_previous = node
    
    # Adding the last node to the sink.
    symbol_graph[symbol_sink].add(convert_str_to_Symbol(symbols[-1])) 

    if graph_type == SymbolGraphType.NONE_ANY:
        # Add a `EOS_TOKEN` to the SOURCE, since it can be `NONE`.
        # Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `EOS_TOKEN` to `A` and `Z` if `Z` is not connected to any node.
        # (Always add it), if it's connected to some node remove it afterwards.
        # How? During connection, we'll have `EOS_TOKEN` -> `Node` -> replace `EOS_TOKEN` with the antecedent of `EOS_TOKEN`, disconnect antecedent from 'EOS_TOKEN`.
        # Each node has a unique identifier, so we'll always be able to track the right antecedent.

        # [TODO] Add loop Z -> A (connect the SINK to the SOURCE).
        symbol_graph[symbol_source] = symbol_graph[symbol_sink] = symbol_graph[symbol_source].union(symbol_graph[symbol_sink])

        # Add `EOS_TOKEN` to SOURCE and SINK.
        symbol_eot = Symbol('EOS_TOKEN', SymbolType.SPECIAL) 
        symbol_graph[symbol_source].add(symbol_eot)
        symbol_graph[symbol_sink].add(symbol_eot)

    elif graph_type == SymbolGraphType.NONE_ONCE:
       # Add `EOS_TOKEN` to the SOURCE
        symbol_eot = Symbol('EOS_TOKEN', SymbolType.SPECIAL) 
        symbol_graph[symbol_source].add(symbol_eot)


    return symbol_graph

def merge_dicts(symbol_graph_sink: dict[Symbol, set[Symbol]], symbol_graph_source: dict[Symbol, set[Symbol]]) -> dict[Symbol, set[Symbol]]:
    merged_dict = defaultdict(set)
    # `|` operator iterates through both key and removes duplicates.
    for key in symbol_graph_sink.keys() | symbol_graph_source.keys():
        merged_dict[key] = symbol_graph_sink[key] | symbol_graph_source[key]
    return merged_dict

def find_antecedent(symbol_graph: dict[Symbol, set[Symbol]], search_symbol: Symbol):
    for key, symbol_set in symbol_graph.items():
        if search_symbol in symbol_set:
            return key

def connect_symbol_graph(symbol_graph_sink: dict[Symbol, set[Symbol]], symbol_graph_source: dict[Symbol, set[Symbol]]) -> dict[Symbol, set[Symbol]]:
    # [CAUTION] There could be common elements in the SOURCE and SINK (loops).
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

            # Need to deal with the `EOS_TOKEN` case for `NONE_ANY` types of graphs. 
            if symbol_sink_elem.content == 'EOS_TOKEN':

                # Search for antecedent of `EOS_TOKEN`.
                symbol_antecedent = find_antecedent(symbol_graph_output, symbol_sink_elem)

                symbol_graph_output[symbol_antecedent].discard(symbol_sink_elem) # type: ignore 
                symbol_graph_output[symbol_antecedent].add(symbol_source_elem) # type: ignore

                continue 

            symbol_graph_output[symbol_sink_elem].add(symbol_source_elem)

    return symbol_graph_output

def check_definition(symbol_def: str):
    # [TODO] Throws the corresponding exceptions.
    pass

# [TODO] Need additional ( ) for `build_full_graph` to work.
def add_spaces_around_brackets(symbol_def: str):
    brackets = ['[', ']', '{', '}', '(', ')']
    
    for bracket in brackets:
        symbol_def = symbol_def.replace(bracket, ' ' + bracket + ' ')

    return symbol_def

def convert_str_def_to_str_queue(symbol_def: str) -> Deque[str]:
    check_definition(symbol_def)

    symbols = add_spaces_around_brackets(symbol_def).split()
    
    queue = deque()
    for symbol in symbols:
       queue.append(symbol) 

    return queue

# Start with empty node, fill it in until reaching (, create new empty node and connect..?
def build_full_symbol_graph(queue_symbol_def: Deque[str]):

    partial: list[str] = []
    while True:
        str_symbol = queue_symbol_def.popleft()
        
        if str_symbol in ('(', '[', '{'):
            # Temporary solution, `construct_symbol_graph` should just take a list of strings.
            symbol_graph_base = construct_symbol_graph(''.join(partial))

            queue_symbol_def.popleft()

            symbol_graph_top = build_full_symbol_graph(queue_symbol_def)

            return connect_symbol_graph(symbol_graph_base, symbol_graph_top)

        elif str_symbol == '}':
            queue_symbol_def.popleft()

            return construct_symbol_graph(''.join(partial), SymbolGraphType.NONE_ANY) 
       
        elif str_symbol == ']':
            queue_symbol_def.popleft()

            return construct_symbol_graph(''.join(partial), SymbolGraphType.NONE_ONCE) 

        elif str_symbol == ')':
            queue_symbol_def.popleft()

            return construct_symbol_graph(''.join(partial)) 

        partial.append(str_symbol)

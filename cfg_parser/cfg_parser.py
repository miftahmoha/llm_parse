from collections import defaultdict
from typing import Deque

from cfg_parser.base import OrderedSet, Symbol, SymbolType, SymbolGraphType
from cfg_parser.functions import (
    convert_str_to_symbol,
    convert_str_def_to_str_queue,
    find_symbol_antecedent,
    get_source_and_sink_special_symbols,
    get_source_and_sink_symbols_content,
)
from cfg_parser.draw import draw_symbol_graph


def construct_symbol_subgraph(
    symbols: list[str], graph_type: SymbolGraphType = SymbolGraphType.STANDARD
) -> dict[Symbol, OrderedSet[Symbol]]:
    # (1) Separates strings, separator is ` `.
    # (2) Should be executed in a nested manner, between each ().

    symbol_graph = defaultdict(OrderedSet)

    if len(symbols) == 0:
        return symbol_graph

    # Useful in connecting graphs.
    symbol_source = Symbol("SOURCE", SymbolType.SPECIAL)
    symbol_sink = Symbol("SINK", SymbolType.SPECIAL)

    symbol_previous = symbol_source
    for symbol_str in symbols:

        if symbol_str == "|":
            symbol_graph[symbol_sink].add(symbol_previous)
            symbol_previous = symbol_source
            continue

        node = convert_str_to_symbol(symbol_str)

        symbol_graph[symbol_previous].add(node)

        symbol_previous = node

    # Adding the last node to the sink.
    symbol_graph[symbol_sink].add(symbol_previous)

    if graph_type == SymbolGraphType.NONE_ANY:
        # Add a `EOS_TOKEN` to the SOURCE, since it can be `NONE`.
        # Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `EOS_TOKEN` to `A` and `Z` (symbols should be different) if `Z` is not connected to any node (always add it, if it's connected to some node remove it afterwards while connecting the graphs)
        # How?
        # During connection, we'll have `EOS_TOKEN` -> `Node` -> replace `EOS_TOKEN` with the antecedent of `EOS_TOKEN`, disconnect antecedent from 'EOS_TOKEN`.
        # Each node has a unique identifier, so we'll always be able to track the right antecedent.

        # Create a `SPECIAL` symbol `EOS_TOKEN for both `SOURCE` and `SINK`, they're conceptually diffrent.
        symbol_eos_source = Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        symbol_eos_sink = Symbol("EOS_TOKEN", SymbolType.SPECIAL)

        # Connecting the loop
        symbol_graph_source, symbol_graph_sink = get_source_and_sink_symbols_content(
            symbol_graph
        )

        for symbol_sink_elem in symbol_graph_sink:
            for symbol_source_elem in symbol_graph_source:
                symbol_graph[symbol_sink_elem].add(symbol_source_elem)

            symbol_graph[symbol_sink_elem].add(symbol_eos_sink)

        # Add a `EOS_TOKEN` to the `SOURCE`, since it can be `NONE`.
        symbol_graph[symbol_source].add(symbol_eos_source)
        # `SINK` will be `EOS_TOKEN` only, since it has to stop at some point (gets removed
        # if the graph of type `NONE_ANY` is connected to some other graph).
        symbol_graph[symbol_sink] = OrderedSet([symbol_eos_sink])

    elif graph_type == SymbolGraphType.NONE_ONCE:
        # Add a `EOS_TOKEN` to the SOURCE, since it can be `NONE`.
        # Add `EOS_TOKEN` to the SOURCE.
        symbol_eos = Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        symbol_graph[symbol_source].add(symbol_eos)

    return symbol_graph


def connect_symbol_graph(
    symbol_graph_left: dict[Symbol, OrderedSet[Symbol]],
    symbol_graph_right: dict[Symbol, OrderedSet[Symbol]],
) -> dict[Symbol, OrderedSet[Symbol]]:
    if not symbol_graph_left and not symbol_graph_right:
        return defaultdict(OrderedSet)

    elif not symbol_graph_left:
        return symbol_graph_right

    elif not symbol_graph_right:
        return symbol_graph_left

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_left_copy = symbol_graph_left.copy()
    symbol_graph_right_copy = symbol_graph_right.copy()

    # Retrieves the special symbols `SOURCE` and `SINK`, they're unique to each `symbol_graph`.
    _, symbol_special_sink_left_copy = get_source_and_sink_special_symbols(
        symbol_graph_left_copy
    )
    symbol_special_source_right_copy, _ = get_source_and_sink_special_symbols(
        symbol_graph_right_copy
    )

    symbol_graph_right_source_copy = symbol_graph_right_copy[
        symbol_special_source_right_copy
    ]
    symbol_graph_right_copy.pop(symbol_special_source_right_copy)

    symbol_graph_left_sink_copy = symbol_graph_left[symbol_special_sink_left_copy]
    symbol_graph_left_copy.pop(symbol_special_sink_left_copy)

    # Merges two `symbol_graphs`, the left without its `SINK` and the right without its `SOURCE`.
    symbol_graph_output = symbol_graph_left_copy | symbol_graph_right_copy

    for symbol_sink_elem in symbol_graph_left_sink_copy:

        symbol_antecedent = (
            find_symbol_antecedent(symbol_graph_output, symbol_sink_elem)
            if symbol_sink_elem.content == "EOS_TOKEN"
            else symbol_sink_elem
        )

        for symbol_source_elem in symbol_graph_right_source_copy:
            symbol_graph_output[symbol_antecedent].add(symbol_source_elem)

        symbol_graph_output[symbol_antecedent].discard(symbol_sink_elem)

    return symbol_graph_output


def union_symbol_graph(
    symbol_graph_left: dict[Symbol, OrderedSet[Symbol]],
    symbol_graph_right: dict[Symbol, OrderedSet[Symbol]],
) -> dict[Symbol, OrderedSet[Symbol]]:
    if not symbol_graph_left and not symbol_graph_right:
        return defaultdict(OrderedSet)

    elif not symbol_graph_left:
        return symbol_graph_right

    elif not symbol_graph_right:
        return symbol_graph_left

    symbol_special_source = Symbol("SOURCE", SymbolType.SPECIAL)
    symbol_special_sink = Symbol("SINK", SymbolType.SPECIAL)

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_left_copy = symbol_graph_left.copy()
    symbol_graph_right_copy = symbol_graph_right.copy()

    # Retrieves the content of `SOURCE` and `SINK` for the right symbol graph.
    symbol_graph_right_source_copy, symbol_graph_right_sink_copy = (
        get_source_and_sink_symbols_content(symbol_graph_right_copy)
    )

    # Retrieves the content of `SOURCE` and `SINK` for the left symbol graph.
    symbol_graph_left_source_copy, symbol_graph_left_sink_copy = (
        get_source_and_sink_symbols_content(symbol_graph_left_copy)
    )

    # Retrieves the special symbols `SOURCE` and `SINK` for the left symbol graph.
    symbol_special_source_left_copy, symbol_special_sink_left_copy = (
        get_source_and_sink_special_symbols(symbol_graph_left_copy)
    )

    symbol_graph_left_copy.pop(symbol_special_source_left_copy)
    symbol_graph_left_copy.pop(symbol_special_sink_left_copy)

    # Retrieves the special symbols `SOURCE` and `SINK` for the right symbol graph.
    symbol_special_source_right_copy, symbol_special_sink_right_copy = (
        get_source_and_sink_special_symbols(symbol_graph_right_copy)
    )
    symbol_graph_right_copy.pop(symbol_special_source_right_copy)
    symbol_graph_right_copy.pop(symbol_special_sink_right_copy)

    # Merges two `symbol_graphs`, both without their `SOURCE` and `SINK`.
    symbol_graph_output = symbol_graph_left_copy | symbol_graph_right_copy

    # Extend the left `SOURCE` to the right `SOURCE`, `|` is not used because it discards the order (important for testing).
    symbol_graph_left_source_copy.extend(symbol_graph_right_source_copy)
    symbol_graph_output[symbol_special_source] = symbol_graph_left_source_copy

    # Extend the left `SINK` to the right `SINK`, `|` is not used because it discards the order (important for testing).
    symbol_graph_left_sink_copy.extend(symbol_graph_right_sink_copy)
    symbol_graph_output[symbol_special_sink] = symbol_graph_left_sink_copy

    return symbol_graph_output


# We construct symbol graphs through their subgraphs, it means that their properties will not change while going through the whole definition.                                            198 # We can connect them, union them but can't modify the structure of the whole symbol graph.                                                                                               199                                                                                                                                                                                           200 # This shouldn't be always true, delimiters like '"["', '"]"', '"{"' and '"}"' force the subgraphs to change.
# If we parse the following definition: """ "(" expression {(factor "-") | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """
# The subgraph (factor "-") | {Regex([0-9]*.[0-9]*) factor | "+" expression} being delimitered with a {} will enforce changes within the structure of the subgraph.


# In such cases, we want to be able to capture those changes, that's when we'll `cast` the symbol graph to whatever delimiter it encouters.
def cast_symbol_graph(
    symbol_graph: dict[Symbol, OrderedSet[Symbol]],
    symbol_graph_cast_type: SymbolGraphType,
) -> dict[Symbol, OrderedSet[Symbol]]:
    symbol_graph_copy = symbol_graph.copy()

    if symbol_graph_cast_type == SymbolGraphType.NONE_ANY:
        symbol_graph_source_copy, symbol_graph_sink_copy = (
            get_source_and_sink_symbols_content(symbol_graph_copy)
        )

        # Makes the 'SINK` loop over the `SOURCE`.
        for symbol_sink_elem in symbol_graph_sink_copy:
            symbol_antecedent = (
                find_symbol_antecedent(symbol_graph_copy, symbol_sink_elem)
                if symbol_sink_elem.content == "EOS_TOKEN"
                else symbol_sink_elem
            )

            for symbol_source_elem in symbol_graph_source_copy:
                if symbol_source_elem.content != "EOS_TOKEN":
                    symbol_graph_copy[symbol_antecedent].add(symbol_source_elem)

        return symbol_graph_copy

    elif symbol_graph_cast_type == SymbolGraphType.NONE_ONCE:
        symbol_special_source_copy, _ = get_source_and_sink_special_symbols(
            symbol_graph_copy
        )
        symbol_graph_source_copy, _ = get_source_and_sink_symbols_content(
            symbol_graph_copy
        )

        for symbol_source_elem in symbol_graph_source_copy:
            if symbol_source_elem.content == "EOS_TOKEN":
                return symbol_graph_copy

        symbol_graph_copy[symbol_special_source_copy].add(
            Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        )

        return symbol_graph_copy

    else:
        return symbol_graph_copy


def build_symbol_graph(symbol_def: str) -> dict[Symbol, OrderedSet[Symbol]]:  # type: ignore
    queue_symbol_def = convert_str_def_to_str_queue(symbol_def)
    LAST_DELIMITER_TYPE: SymbolGraphType = SymbolGraphType.STANDARD

    def recurse_build(queue_symbol_def: Deque[str]):
        partial: list[str] = []
        symbol_graph_partial_lhs: dict[Symbol, OrderedSet[Symbol]] = {}
        nonlocal LAST_DELIMITER_TYPE
        LAST_DELIMITER_TYPE_LOCAL: SymbolGraphType = LAST_DELIMITER_TYPE
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "{"):
                if str_symbol == "(":
                    LAST_DELIMITER_TYPE = SymbolGraphType.STANDARD
                elif str_symbol == "{":
                    LAST_DELIMITER_TYPE = SymbolGraphType.NONE_ANY
                elif str_symbol == "[":
                    LAST_DELIMITER_TYPE = SymbolGraphType.NONE_ONCE

                symbol_graph_base = construct_symbol_subgraph(partial)

                # What happens if `partial` is not cleared?

                # Let's have a look at the following example: (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_)

                # Each (_NUM should be looked at as a stack,

                # If, within the same stack, the graph (_1 ... 1_) is separated by another stack (_2 `def_2` 2_),
                # We'll use the terminology `symbol_graph_partial_lhs` for the left part `def_1` and `symbol_graph_partial_rhs`
                # for the right part `def_3`.

                # If there is no such separation, `symbol_graph_partial_lhs` is empty and `symbol_graph_partial_rhs` will
                # represent the subgraph instead.

                # After we connect `def_1` and `def_2` into`symbol_graph_partial_lhs`, we'll jump into next iteration
                # and start building the `def_3`, if partial is not cleared we'll build `def_1 + def_3` instead of only `def_3`.

                # We'll build (_1 `def_1` (_2 `def_2` 2_) `def_1` `def_3` ) 1_) instead of (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_).
                partial.clear()

                symbol_graph_top = recurse_build(queue_symbol_def)

                symbol_graph_partial_lhs = connect_symbol_graph(
                    symbol_graph_base, symbol_graph_top
                )

                # Avoids leaving the the `lower` level stack after terminating a `higher` level stack.
                # If we do leave, `symbol_graph_partial_rhs` will not be constructed if it exists!
                # If it doesn't exist, then we return the `symbol_graph_partial_lhs`.
                if bool(queue_symbol_def):

                    # Dealing with sequences of delimiters (_1 `def_1` (_2 `def_2` 2_) {_3 `def_3` 3_} (_4 `def_4` 4_) `def_5` 1_).
                    if queue_symbol_def[0] in ("(", "[", "{"):
                        symbol_graph_next_delim = recurse_build(queue_symbol_def)
                        symbol_graph_partial_lhs = connect_symbol_graph(
                            symbol_graph_partial_lhs, symbol_graph_next_delim
                        )

                    continue

                # We need to return at the last delimiter to not pop from an empty queue,
                # the expression needs to be correct syntactically.
                return symbol_graph_partial_lhs

            # -- Case 1: `symbol_graph_partial_lhs` is not empty and `symbol_graph_partial_rhs` is not empty:
            # (_1 `def_1` (_2 `def_2` _2) `def_3` _1), `def_1` and `def_2` will be connected into `symbol_graph_partial_lhs`,
            # the rest def_3 will be set to `symbol_graph_partial_rhs` and connect_symbol_graph(symbol_graph_partial_lhs, symbol_graph_partial_rhs) is returned.
            # -- Case 2: `symbol_graph_partial_lhs` is not empty and `symbol_graph_partial_rhs` is empty:
            # (_1 `def_1` (_2 `def_2` _2) _1), `def_1` and `def_2` will be connected into `symbol_graph_partial_lhs`, since `partial` is cleared
            # `symbol_graph_partial_rhs` will be empty and and connect_symbol_graph(symbol_graph_partial_lhs, symbol_graph_partial_rhs)
            # will return symbol_graph_partial_lhs.
            # -- Case 3: `symbol_graph_partial_lhs` is empty and `symbol_graph_partial_rhs` is not empty:
            # It means that there is a righthand side without a lefthand side, it's impossible.
            # -- Case 4: `symbol_graph_partial_lhs` is empty and `symbol_graph_partial_rhs` is empty:
            # ()
            # Same logic applies to "]" and "}".
            elif str_symbol == ")":
                symbol_graph_partial_rhs = construct_symbol_subgraph(partial)
                return connect_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )

            elif str_symbol == "}":
                symbol_graph_partial_rhs = construct_symbol_subgraph(
                    partial, SymbolGraphType.NONE_ANY
                )
                symbol_graph_out = connect_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )
                return cast_symbol_graph(symbol_graph_out, SymbolGraphType.NONE_ANY)
                # return connect_symbol_graph(
                #     symbol_graph_partial_lhs, symbol_graph_partial_rhs
                # )

            elif str_symbol == "]":
                symbol_graph_partial_rhs = construct_symbol_subgraph(
                    partial, SymbolGraphType.NONE_ONCE
                )
                symbol_graph_out = connect_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )
                return cast_symbol_graph(symbol_graph_out, SymbolGraphType.NONE_ONCE)
                # return connect_symbol_graph(
                # symbol_graph_partial_lhs, symbol_graph_partial_rhs
                # )

            elif str_symbol == "|":
                # This means that the `|` is inside a stack not between stacks.
                # Example of (inside a stack): (_1 `subdef_1` | `subdef_2` 1_).
                # Example of (between stacks):
                # (_1 (_2 `def_1` _2) | (_3 `def_3` _3)  1_)
                # or (_1 (_2 `def_1` _2) | def_2  1_).

                # Need information of the last delimiter ('(', '[' or '{')) to set
                # the construction to the right type, that's where `LAST_DELIMITER_TYPE`
                # comes very handy.
                if not symbol_graph_partial_lhs:
                    symbol_graph_partial_lhs = construct_symbol_subgraph(
                        partial, LAST_DELIMITER_TYPE
                    )

                symbol_graph_partial_rhs = recurse_build(queue_symbol_def)
                symbol_graph_out = union_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )
                return cast_symbol_graph(symbol_graph_out, LAST_DELIMITER_TYPE_LOCAL)

            partial.append(str_symbol)

    return recurse_build(queue_symbol_def)

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
        # Should add a `EOS_TOKEN` to `A` and `Z` if `Z` is not connected to any node.
        # (Always add it), if it's connected to some node remove it afterwards.
        # How? During connection, we'll have `EOS_TOKEN` -> `Node` -> replace `EOS_TOKEN` with the antecedent of `EOS_TOKEN`, disconnect antecedent from 'EOS_TOKEN`.
        # Each node has a unique identifier, so we'll always be able to track the right antecedent.

        # [TODO] Add loop Z -> A (connect the SINK to the SOURCE).
        symbol_graph[symbol_source] = symbol_graph[symbol_sink] = (
            symbol_graph[symbol_source] | symbol_graph[symbol_sink]
        )

        # Add `EOS_TOKEN` to SOURCE and SINK.
        symbol_eot = Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        symbol_graph[symbol_source].add(symbol_eot)
        symbol_graph[symbol_sink].add(symbol_eot)

    elif graph_type == SymbolGraphType.NONE_ONCE:
        # Add a `EOS_TOKEN` to the SOURCE, since it can be `NONE`.
        # Add `EOS_TOKEN` to the SOURCE
        symbol_eot = Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        symbol_graph[symbol_source].add(symbol_eot)

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

    # Avoid modifying the original dicts.
    symbol_graph_left_copy = symbol_graph_left.copy()
    symbol_graph_right_copy = symbol_graph_right.copy()

    # Retrieves the special symbols `SOURCE` and `SINK`, they're unique to each `symbol_graph`.
    _, symbol_special_sink_left = get_source_and_sink_special_symbols(symbol_graph_left)
    symbol_special_source_right, _ = get_source_and_sink_special_symbols(
        symbol_graph_right
    )

    symbol_graph_right_source = symbol_graph_right[symbol_special_source_right]
    symbol_graph_right_copy.pop(symbol_special_source_right)

    symbol_graph_left_sink = symbol_graph_left[symbol_special_sink_left]
    symbol_graph_left_copy.pop(symbol_special_sink_left)

    # Merges two `symbol_graphs`, the left without its `SINK` and the right without its `SOURCE`.
    # symbol_graph_output = symbol_graph_left | symbol_graph_right
    symbol_graph_output = symbol_graph_left_copy | symbol_graph_right_copy

    for symbol_sink_elem in symbol_graph_left_sink:
        for symbol_source_elem in symbol_graph_right_source:

            # Avoids duplicates, (SINK) -> OrderedSet{(1), (2)}; (SOURCE) -> OrderedSet{(1), (?)} >>>>>> AVOIDS (1) -> (1).
            # if symbol_sink_elem == symbol_source_elem:
            # continue

            # Need to deal with the `EOS_TOKEN` case for `NONE_ANY` types of graphs.
            if symbol_sink_elem.content == "EOS_TOKEN":

                # Search for antecedent of `EOS_TOKEN`.
                symbol_antecedent = find_symbol_antecedent(
                    symbol_graph_output, symbol_sink_elem
                )

                symbol_graph_output[symbol_antecedent].discard(symbol_sink_elem)  # type: ignore
                symbol_graph_output[symbol_antecedent].add(symbol_source_elem)  # type: ignore

                continue

            symbol_graph_output[symbol_sink_elem].add(symbol_source_elem)

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

    # Avoid modifying the original dicts.
    symbol_graph_left_copy = symbol_graph_left.copy()
    symbol_graph_right_copy = symbol_graph_right.copy()

    # Retrieves the special symbols `SOURCE` and `SINK` for the left graph.
    symbol_graph_right_source, symbol_graph_right_sink = (
        get_source_and_sink_symbols_content(symbol_graph_right)
    )

    # Retrieves the special symbols `SOURCE` and `SINK` for the left graph.
    symbol_graph_left_source, symbol_graph_left_sink = (
        get_source_and_sink_symbols_content(symbol_graph_left)
    )

    # Retrieves the content of `SOURCE` and `SINK` for the left symbol graph.
    symbol_special_source_left, symbol_special_sink_left = (
        get_source_and_sink_special_symbols(symbol_graph_left)
    )
    symbol_graph_left_copy.pop(symbol_special_source_left)
    symbol_graph_left_copy.pop(symbol_special_sink_left)

    # Retrieves the content of `SOURCE` and `SINK` for the left symbol graph.
    symbol_special_source_right, symbol_special_sink_right = (
        get_source_and_sink_special_symbols(symbol_graph_right)
    )
    symbol_graph_right_copy.pop(symbol_special_source_right)
    symbol_graph_right_copy.pop(symbol_special_sink_right)

    # Merges two `symbol_graphs`, the left without its `SINK` and the right without its `SOURCE`.
    symbol_graph_output = symbol_graph_left_copy | symbol_graph_right_copy

    # Extend the left `SOURCE` to the right `SOURCE`, `|` is not used because it discards the order.
    symbol_graph_left_source.extend(symbol_graph_right_source)
    symbol_graph_output[symbol_special_source] = symbol_graph_left_source

    # Extend the left `SINK` to the right `SINK`, `|` is not used because it discards the order.
    symbol_graph_left_sink.extend(symbol_graph_right_sink)
    symbol_graph_output[symbol_special_sink] = symbol_graph_left_sink

    return symbol_graph_output


def build_symbol_graph(symbol_def: str) -> dict[Symbol, OrderedSet[Symbol]]:  # type: ignore
    queue_symbol_def = convert_str_def_to_str_queue(symbol_def)

    def recurse_build(queue_symbol_def: Deque[str]):
        partial: list[str] = []
        symbol_graph_partial_lhs: dict[Symbol, OrderedSet[Symbol]] = {}
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "{"):
                symbol_graph_base = construct_symbol_subgraph(partial)
                # **************** What happens if `partial` is not cleared? ****************

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

                if bool(queue_symbol_def):
                    continue

                return symbol_graph_partial_lhs

            elif str_symbol == "}":
                return construct_symbol_subgraph(partial, SymbolGraphType.NONE_ANY)

            elif str_symbol == "]":
                return construct_symbol_subgraph(partial, SymbolGraphType.NONE_ONCE)

            elif str_symbol == ")":
                symbol_graph_partial_rhs = construct_symbol_subgraph(partial)
                return connect_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )

            elif str_symbol == "|":
                # This means that the `|` is inside a stack not between stacks.
                # Example of (inside a stack): (_1 `subdef_1` | `subdef_2` 1_).
                # Example of (between stacks):
                # (_1 (_2 `def_1` _2) | (_3 `def_3` _3)  1_)
                # or (_1 (_2 `def_1` _2) | def_2  1_).

                if not symbol_graph_partial_lhs:
                    symbol_graph_partial_lhs = construct_symbol_subgraph(partial)

                symbol_graph_partial_rhs = recurse_build(queue_symbol_def)

                return union_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )

            partial.append(str_symbol)

    return recurse_build(queue_symbol_def)

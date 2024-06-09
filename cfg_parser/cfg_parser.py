from collections import defaultdict
from typing import Deque, cast

from cfg_parser.base import OrderedSet, Symbol, SymbolType, SymbolGraph, SymbolGraphType
from cfg_parser.functions import (
    convert_str_to_symbol,
    convert_str_def_to_str_queue,
    get_symbol_antecedent,
    get_symbol_antecedents,
    get_symbols_with_content,
    discard_single_nodes,
    is_contain_eos_token,
)
from cfg_parser.draw import draw_symbol_graph


def construct_symbol_subgraph(
    symbols_str: list[str], graph_type: SymbolGraphType = SymbolGraphType.STANDARD
) -> SymbolGraph:
    symbol_graph = SymbolGraph()

    if len(symbols_str) == 0:
        return symbol_graph

    # INITIALS
    initial = convert_str_to_symbol(symbols_str[0])
    symbol_graph.initials.add(initial)

    # Single node
    if len(symbols_str) == 1:
        symbol_graph.initials, symbol_graph.finals = OrderedSet([initial]), OrderedSet(
            [initial]
        )
        # Node without connections
        symbol_graph.nodes[initial]
        return symbol_graph

    symbol_previous = initial
    for symbol_str in symbols_str[1:]:

        if symbol_str == "|":
            symbol_graph.finals.add(symbol_previous)
            continue

        node = convert_str_to_symbol(symbol_str)

        if symbol_previous in symbol_graph.finals:
            symbol_graph.initials.add(node)
            symbol_previous = node
            continue

        symbol_graph.nodes[symbol_previous].add(node)

        symbol_previous = node

    # FINALS
    symbol_graph.finals.add(symbol_previous)

    return cast_symbol_graph(symbol_graph, graph_type)


def connect_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.nodes and not symbol_graph_rhs.nodes:
        return SymbolGraph()

    elif not symbol_graph_lhs.nodes:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.nodes:
        return symbol_graph_lhs

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Single node symbols will connect through their `INITIALS` and `FINALS`.
    symbol_graph_lhs_copy.nodes = discard_single_nodes(symbol_graph_lhs_copy.nodes)
    symbol_graph_rhs_copy.nodes = discard_single_nodes(symbol_graph_rhs_copy.nodes)

    # Union the connections between both symbol graphs.
    symbol_graph_nodes_out = symbol_graph_lhs_copy.nodes | symbol_graph_rhs_copy.nodes

    # Connect the left `FINALS` (also takes care of `EOS_TOKENS`) with the right `INITIALS`.
    for symbol_final in symbol_graph_lhs_copy.finals:

        if symbol_final.content == "EOS_TOKEN":
            symbol_antecedents = get_symbol_antecedents(
                symbol_graph_nodes_out, symbol_final
            )
            # Discarding the connection to `EOS_TOKEN` symbol.
            for symbol_antecedent in symbol_antecedents:
                symbol_graph_nodes_out[symbol_antecedent].discard(symbol_final)
            symbol_final = symbol_antecedents

        if not isinstance(symbol_final, list):
            symbol_final = [symbol_final]

        for symbol_initial in symbol_graph_rhs_copy.initials:
            for final in symbol_final:
                symbol_graph_nodes_out[final].add(symbol_initial)

    # Keeps the initials from the left symbol graph and the finals from the right symbol graph.
    symbol_graph_initials_out = symbol_graph_lhs_copy.initials
    symbol_graph_finals_out = symbol_graph_rhs_copy.finals

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        nodes=symbol_graph_nodes_out,
        finals=symbol_graph_finals_out,
    )


def union_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.nodes and not symbol_graph_rhs.nodes:
        return SymbolGraph()

    elif not symbol_graph_lhs.nodes:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.nodes:
        return symbol_graph_lhs

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Extend the left `INITIALS` to the right `INITIALS`, `|` is not used because it discards the order (*for testing).

    # Removes duplicates (if they exist) `EOS_TOKEN` symbols from `INITIALS`.
    if is_contain_eos_token(symbol_graph_lhs_copy.initials) and is_contain_eos_token(
        symbol_graph_rhs_copy.initials
    ):
        symbol_special_eos_token = get_symbols_with_content(
            symbol_graph_rhs_copy.initials, "EOS_TOKEN"
        )
        symbol_graph_rhs_copy.initials.discard(symbol_special_eos_token[0])

    symbol_graph_initials_out = symbol_graph_lhs_copy.initials.extend(
        symbol_graph_rhs_copy.initials
    )

    # Union two `symbol_graphs`, both without their `INITIALS` and `FINALS`.
    symbol_graph_nodes_out = symbol_graph_lhs_copy.nodes | symbol_graph_rhs_copy.nodes

    # Extend the left `FINALS` to the right `FINALS`, `|` is not used because it discards the order (*for testing).
    symbol_graph_finals_out = symbol_graph_lhs_copy.finals.extend(
        symbol_graph_rhs_copy.finals
    )

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        nodes=symbol_graph_nodes_out,
        finals=symbol_graph_finals_out,
    )


# Delimiters such as `NONE_ANY "{XXXXX}"`, `NONE_ONE [XXXXX]` can enduce changes in the structure that the connection and the union can't express.


# For example when `NONE_ANY` delimiters nest a composite definition such as (factor "-") | {Regex([0-9]*.[0-9]*) factor | "+" expression},
# there'll be new connections, one of them is '"-"' being connected to Regex([0-9]*.[0-9]*) and '"+"'. `cast_symbol_graph` will add those remaining connections.
def cast_symbol_graph(
    symbol_graph: SymbolGraph,
    symbol_graph_cast_type: SymbolGraphType,
) -> SymbolGraph:
    symbol_graph_copy = symbol_graph.copy()

    if symbol_graph_cast_type == SymbolGraphType.NONE_ANY:
        # Add a `EOS_TOKEN` to the `initials`, since it can be `NONE`.
        # Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `EOS_TOKEN` to `A` and `Z` (symbols should be different) if `Z` is not connected to any node (always add it, if it's connected to some node remove it afterwards while connecting the graphs)
        # How?
        # During connection, we'll have `EOS_TOKEN` -> `Node` -> replace `EOS_TOKEN` with the antecedent of `EOS_TOKEN`, disconnect antecedent from 'EOS_TOKEN`.
        # Each node has a unique identifier, so we'll always be able to track the right antecedent.

        for symbol_final in symbol_graph_copy.finals:
            if symbol_final.content == "EOS_TOKEN":
                # [PERFORMANCE] Could raise a flag here and avoid calling is_contain_eos_token(symbol_graph_copy.finals).
                symbol_antecedent = get_symbol_antecedent(
                    symbol_graph_copy.nodes, symbol_final
                )

                # Removing the `EOS_TOKEN` node.
                # [NOTE(to me)]I don't think it should be removed, if a subgraph of type `NONE_ANY` in inside a graph `NON_ANY`,
                # you still want to have the `EOS_TOKEN` in the subgraph.
                # del symbol_graph_copy[symbol_final]

                # Removing the connection of the antecedent with `EOS_TOKEN`.
                # symbol_graph_copy.nodes[symbol_antecedent].discard(symbol_final)
                symbol_final = symbol_antecedent

            # [TODO] Commentary.
            for symbol_initial in symbol_graph_copy.initials:
                if symbol_initial.content == "EOS_TOKEN":
                    continue
                symbol_graph_copy.nodes[symbol_final].add(symbol_initial)

        if is_contain_eos_token(symbol_graph_copy.initials) and is_contain_eos_token(
            symbol_graph_copy.finals
        ):
            return symbol_graph_copy

        if not is_contain_eos_token(symbol_graph_copy.initials):
            # `EOS_TOKEN` symbol for the initials.
            symbol_special_eos_initial = Symbol("EOS_TOKEN", SymbolType.SPECIAL)

            # Add `EOS_TOKEN` as `initials`.
            symbol_graph_copy.initials.add(symbol_special_eos_initial)

            # Add `EOS_TOKEN` as node.
            symbol_graph_copy.nodes[symbol_special_eos_initial]

        if not is_contain_eos_token(symbol_graph_copy.finals):
            # `EOS_TOKEN` symbols for the initials and finals.
            symbol_special_eos_final = Symbol("EOS_TOKEN", SymbolType.SPECIAL)

            # Connect the `EOS_TOKEN` in `FINALS` with the elements in the "previous" (before cast) `FINALS`.
            for symbol_final in symbol_graph_copy.finals:
                symbol_graph_copy.nodes[symbol_final].add(symbol_special_eos_final)

            # Clear the finals since the `EOS_TOKEN` will be the only element in the finals.
            symbol_graph_copy.finals = OrderedSet([])

            # Add `EOS_TOKEN` as `finals`.
            symbol_graph_copy.finals.add(symbol_special_eos_final)

            # Add `EOS_TOKEN` as node.
            # symbol_graph_copy.nodes[symbol_special_eos_final]

        return symbol_graph_copy

    elif symbol_graph_cast_type == SymbolGraphType.NONE_ONCE:
        # Add a `EOS_TOKEN` to the SOURCE, since it can be `NONE`.

        # Check if `EOS_TOKEN` already exists.
        for symbol_initial in symbol_graph_copy.initials:
            if symbol_initial.content == "EOS_TOKEN":
                return symbol_graph_copy

        # Add `EOS_TOKEN` as `initials`
        symbol_special_eos_initial = Symbol("EOS_TOKEN", SymbolType.SPECIAL)
        symbol_graph.initials.add(symbol_special_eos_initial)
        symbol_graph.nodes[symbol_special_eos_initial]
        return symbol_graph_copy

    else:
        if is_contain_eos_token(symbol_graph_copy.initials) and is_contain_eos_token(
            symbol_graph_copy.finals
        ):
            return symbol_graph_copy
        return symbol_graph_copy


def build_symbol_graph(symbol_def: str) -> SymbolGraph:  # type: ignore
    queue_symbol_def = convert_str_def_to_str_queue(symbol_def)
    LAST_STACK_GRAPH_TYPE: SymbolGraphType = SymbolGraphType.STANDARD

    def recurse_build(queue_symbol_def: Deque[str]):
        partial: list[str] = []
        symbol_graph_partial_lhs: SymbolGraph = SymbolGraph()
        nonlocal LAST_STACK_GRAPH_TYPE
        CURRENT_STACK_GRAPH_TYPE: SymbolGraphType = LAST_STACK_GRAPH_TYPE
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "{"):
                if str_symbol == "(":
                    LAST_STACK_GRAPH_TYPE = SymbolGraphType.STANDARD
                elif str_symbol == "{":
                    LAST_STACK_GRAPH_TYPE = SymbolGraphType.NONE_ANY
                elif str_symbol == "[":
                    LAST_STACK_GRAPH_TYPE = SymbolGraphType.NONE_ONCE

                symbol_graph_bottom_level = construct_symbol_subgraph(partial)

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

                symbol_graph_upper_level = recurse_build(queue_symbol_def)

                # Always empty inside a stack.
                if not symbol_graph_partial_lhs:
                    symbol_graph_partial_lhs = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )
                else:
                    symbol_graph_partial_lhs_prev = symbol_graph_partial_lhs
                    symbol_graph_partial_lhs = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )
                    symbol_graph_partial_lhs = connect_symbol_graph(
                        symbol_graph_partial_lhs_prev, symbol_graph_bottom_level
                    )

                # Avoids leaving the the `lower` level stack after terminating a `higher` level stack.
                # If we do leave, `symbol_graph_partial_rhs` will not be constructed if it exists!
                # If it doesn't exist, then we return the `symbol_graph_partial_lhs`.
                if bool(queue_symbol_def):

                    # Dealing with sequences of delimiters (_1 `def_1` (_2 `def_2` 2_) {_3 `def_3` 3_} (_4 `def_4` 4_) `def_5` 1_).
                    # Doesn't work for more than two sequences.
                    if queue_symbol_def[0] in ("(", "[", "{"):
                        queue_symbol_def.popleft()
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

            elif str_symbol == "]":
                symbol_graph_partial_rhs = construct_symbol_subgraph(
                    partial, SymbolGraphType.NONE_ONCE
                )
                symbol_graph_out = connect_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )
                return cast_symbol_graph(symbol_graph_out, SymbolGraphType.NONE_ONCE)

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
                        partial, LAST_STACK_GRAPH_TYPE
                    )

                symbol_graph_partial_rhs = recurse_build(queue_symbol_def)
                symbol_graph_out = union_symbol_graph(
                    symbol_graph_partial_lhs, symbol_graph_partial_rhs
                )
                return cast_symbol_graph(symbol_graph_out, CURRENT_STACK_GRAPH_TYPE)

            partial.append(str_symbol)

    return recurse_build(queue_symbol_def)

from typing import Deque

from cfg_parse.base import OrderedSet, Symbol, SymbolGraph, SymbolGraphType, SymbolType
from cfg_parse.cfg_build.helpers import (
    _convert_str_def_to_str_queue,
    _convert_str_to_symbol,
    _discard_single_nodes_from_tree,
    _get_symbol_predecessors,
    _get_symbol_from_content_attr,
    _tree_contains_eos_symbol,
)


def construct_symbol_subgraph(
    symbols_str: list[str], graph_type: SymbolGraphType = SymbolGraphType.STANDARD
) -> SymbolGraph:
    symbol_graph = SymbolGraph()

    # Empty symbol graph.
    if len(symbols_str) == 0:
        return symbol_graph

    # INITIALS
    initial = _convert_str_to_symbol(symbols_str[0])
    # Add the node to the initials.
    symbol_graph.initials.add(initial)
    # Add the node to the symbol graph.
    symbol_graph.tree[initial]

    # Single node
    if len(symbols_str) == 1:
        symbol_graph.initials, symbol_graph.finals = OrderedSet([initial]), OrderedSet(
            [initial]
        )
        # Node without connections
        symbol_graph.tree[initial]
        return symbol_graph

    symbol_previous = initial
    for symbol_str in symbols_str[1:]:
        if symbol_str == "|":
            symbol_graph.finals.add(symbol_previous)
            continue

        node = _convert_str_to_symbol(symbol_str)

        if symbol_previous in symbol_graph.finals:
            # Add the node to the initials.
            symbol_graph.initials.add(node)
            # Add the node to the symbol graph
            symbol_graph.tree[node]
            symbol_previous = node
            continue

        symbol_graph.tree[symbol_previous].add(node)

        symbol_previous = node

    # FINALS
    # Add the node to the finals.
    symbol_graph.finals.add(symbol_previous)

    return cast_symbol_graph(symbol_graph, graph_type)


def connect_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Single node symbols will connect through their `INITIALS` and `FINALS`.
    symbol_graph_lhs_copy.tree = _discard_single_nodes_from_tree(
        symbol_graph_lhs_copy.tree
    )
    symbol_graph_rhs_copy.tree = _discard_single_nodes_from_tree(
        symbol_graph_rhs_copy.tree
    )

    # Union the connections between both symbol graphs.
    symbol_graph_tree_out = symbol_graph_lhs_copy.tree | symbol_graph_rhs_copy.tree

    # Connect the left `FINALS` (also takes care of `EOS_SYMBOLS`) with the right `INITIALS`.
    for symbol_final in symbol_graph_lhs_copy.finals:
        if symbol_final.content == "EOS_SYMBOL":
            symbol_predecessors = _get_symbol_predecessors(
                symbol_graph_tree_out, symbol_final
            )
            # Discarding the connection to `EOS_SYMBOL` symbol.
            for symbol_predecessor in symbol_predecessors:
                symbol_graph_tree_out[symbol_predecessor].discard(symbol_final)
            symbol_final = symbol_predecessors

        if not isinstance(symbol_final, list):
            symbol_final = [symbol_final]

        for symbol_initial in symbol_graph_rhs_copy.initials:
            for final in symbol_final:
                symbol_graph_tree_out[final].add(symbol_initial)

    # Keeps the initials from the left symbol graph and the finals from the right symbol graph.
    symbol_graph_initials_out = symbol_graph_lhs_copy.initials
    symbol_graph_finals_out = symbol_graph_rhs_copy.finals

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_finals_out,
    )


def union_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Extend the left `INITIALS` to the right `INITIALS`, `|` is not used because it discards the order (*for testing).

    # Removes duplicates (if they exist) `EOS_SYMBOL` symbols from `INITIALS`.
    if _tree_contains_eos_symbol(
        symbol_graph_lhs_copy.initials
    ) and _tree_contains_eos_symbol(symbol_graph_rhs_copy.initials):
        symbol_special_eos_symbol = _get_symbol_from_content_attr(
            symbol_graph_rhs_copy.initials, "EOS_SYMBOL"
        )
        symbol_graph_rhs_copy.initials.discard(symbol_special_eos_symbol[0])

    symbol_graph_initials_out = symbol_graph_lhs_copy.initials.extend(
        symbol_graph_rhs_copy.initials
    )

    # Union two `symbol_graphs`, both without their `INITIALS` and `FINALS`.
    symbol_graph_tree_out = symbol_graph_lhs_copy.tree | symbol_graph_rhs_copy.tree

    # Extend the left `FINALS` to the right `FINALS`, `|` is not used because it discards the order (*for testing).
    symbol_graph_finals_out = symbol_graph_lhs_copy.finals.extend(
        symbol_graph_rhs_copy.finals
    )

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_finals_out,
    )


# Delimiters such as `NONE_ANY`, `NONE_ONE` can enduce changes in the structure that
# the connection and the union can't express.
# For example when `NONE_ANY` delimiters nest a composite definition such as
# (factor "-") | {Regex([0-9]*.[0-9]*) factor | "+" expression},
# there'll be new connections, one of them is '"-"' being connected to Regex([0-9]*.[0-9]*) and '"+"'.
# `cast_symbol_graph` will add those remaining connections.
def cast_symbol_graph(
    symbol_graph: SymbolGraph,
    symbol_graph_cast_type: SymbolGraphType,
) -> SymbolGraph:
    symbol_graph_copy = symbol_graph.copy()

    if symbol_graph_cast_type == SymbolGraphType.NONE_ANY:
        # Add a `EOS_SYMBOL` to the `initials`, since it can be `NONE`.
        # Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `EOS_SYMBOL` to `A` and `Z` (symbols should be different) if `Z` is not connected to any node (always add it, if it's connected to some node remove it afterwards while connecting the graphs)
        # How?
        # During connection, we'll have `EOS_SYMBOL` -> `Node` -> replace `EOS_SYMBOL` with the predecessor of `EOS_SYMBOL`, disconnect predecessor from 'EOS_SYMBOL`.
        # Each node has a unique identifier, so we'll always be able to track the right predecessor.

        for symbol_final in symbol_graph_copy.finals:
            if symbol_final.content == "EOS_SYMBOL":
                # [PERFORMANCE] Could raise a flag here and avoid calling is_contain_EOS_SYMBOL(symbol_graph_copy.finals).
                # symbol_predecessor = get_symbol_predecessor(
                #     symbol_graph_copy.tree, symbol_final
                # )
                symbol_predecessors = _get_symbol_predecessors(
                    symbol_graph_copy.tree, symbol_final
                )

                # Removing the `EOS_SYMBOL` node.
                # [NOTE(to me)]I don't think it should be removed, if a subgraph of type `NONE_ANY` in inside a graph `NON_ANY`,
                # you still want to have the `EOS_SYMBOL` in the subgraph.
                # del symbol_graph_copy[symbol_final]

                # Removing the connection of the predecessor with `EOS_SYMBOL`.
                # symbol_graph_copy.tree[symbol_predecessor].discard(symbol_final)
                # symbol_final = symbol_predecessor
                symbol_final = symbol_predecessors

            if not isinstance(symbol_final, list):
                symbol_final = [symbol_final]

            # [TODO] Commentary.
            for symbol_initial in symbol_graph_copy.initials:
                if symbol_initial.content == "EOS_SYMBOL":
                    continue
                for final in symbol_final:
                    symbol_graph_copy.tree[final].add(symbol_initial)

        if _tree_contains_eos_symbol(
            symbol_graph_copy.initials
        ) and _tree_contains_eos_symbol(symbol_graph_copy.finals):
            return symbol_graph_copy

        if not _tree_contains_eos_symbol(symbol_graph_copy.initials):
            # `EOS_SYMBOL` symbol for the initials.
            symbol_special_eos_initial = Symbol("EOS_SYMBOL", SymbolType.TERMINAL)

            # Add `EOS_SYMBOL` as `initials`.
            symbol_graph_copy.initials.add(symbol_special_eos_initial)

            # Add `EOS_SYMBOL` as node.
            symbol_graph_copy.tree[symbol_special_eos_initial]

        if not _tree_contains_eos_symbol(symbol_graph_copy.finals):
            # `EOS_SYMBOL` symbols for the initials and finals.
            symbol_special_eos_final = Symbol("EOS_SYMBOL", SymbolType.TERMINAL)

            # Connect the `EOS_SYMBOL` in `FINALS` with the elements in the "previous" (before cast) `FINALS`.
            for symbol_final in symbol_graph_copy.finals:
                symbol_graph_copy.tree[symbol_final].add(symbol_special_eos_final)

            # Clear the finals since the `EOS_SYMBOL` will be the only element in the finals.
            symbol_graph_copy.finals = OrderedSet([])

            # Add `EOS_SYMBOL` as `finals`.
            symbol_graph_copy.finals.add(symbol_special_eos_final)

            # Add `EOS_SYMBOL` as node.
            # symbol_graph_copy.tree[symbol_special_eos_final]

        return symbol_graph_copy

    elif symbol_graph_cast_type == SymbolGraphType.NONE_ONCE:
        # Add a `EOS_SYMBOL` to the SOURCE, since it can be `NONE`.

        # Check if `EOS_SYMBOL` already exists.
        for symbol_initial in symbol_graph_copy.initials:
            if symbol_initial.content == "EOS_SYMBOL":
                return symbol_graph_copy

        # Add `EOS_SYMBOL` as `initials`
        symbol_special_eos_initial = Symbol("EOS_SYMBOL", SymbolType.TERMINAL)
        symbol_graph_copy.initials.add(symbol_special_eos_initial)
        symbol_graph_copy.tree[symbol_special_eos_initial]
        return symbol_graph_copy

    else:
        if _tree_contains_eos_symbol(
            symbol_graph_copy.initials
        ) and _tree_contains_eos_symbol(symbol_graph_copy.finals):
            return symbol_graph_copy
        return symbol_graph_copy


def build_symbol_graph(symbol_def: str) -> SymbolGraph:
    queue_symbol_def = _convert_str_def_to_str_queue(symbol_def)

    # We build graphs from the left, (_1 `def_1` (_2 `def_2` 2_) `def_3` (_3 def_4 3_) 1_),
    # Each time, we encounter an opening delimiter `(, [, {`, we build what we accumulated before it.
    # In the example above, there nothing before, thus we're going to build an empty subgraph,
    # let's call it `subgraph_{0}`. `_{}` refers to the stack level.
    # `subgraph_{0}` is stored in a variable called `symbol_graph_bottom_level_{0}`, as you might have guessed,
    # it refers to the bottom stack layer.
    # Because we can look at it as follows:
    # (_0 [EMPTY_GRAPH] --> `symbol_graph_bottom_level_{0}` (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_) 0_)
    # When we reach a new stack layer, in the example `(_2`, we'll recurse through the next stack layer `(_2`
    # and return the result (when we encouter a closing delimiter `), ], }`) to a variable called `symbol_graph_upper_level_{1}`.
    # Then we build `def_2` which'll be returned to symbol_graph_upper_level_{1}`.
    # Finally, It'll be connected to `def_1` and stored into a variable called `symbol_graph_partial_lhs_{1}`.`
    # We repeat the same process within a single stack, we successively build bottom and upper layers,
    # ``def_1` (_2 `def_2` 2_)` and ``def_3` (_3 def_4 3_)` while acummulating the result
    # in `symbol_graph_partial_lhs_{1}` .
    def recurse_build(queue_symbol_def: Deque[str]):
        current_stack_accumulated_symbols: list[str] = []
        current_stack_accumulated_symbol_graph: SymbolGraph = SymbolGraph()
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "{"):
                symbol_graph_bottom_level = construct_symbol_subgraph(
                    current_stack_accumulated_symbols
                )

                # What happens if `current_stack_accumulated_symbols` is not cleared?
                # Let's have a look at the following example: (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_)
                # Each (_NUM should be looked at as a stack,
                # Since we're building accordingly from the left, what'll happen is upon leaving the second
                # stack, we'll have already built and connect `def_1` and `def_2`.
                # Then while consuming the symbols `def_3`, we'll have additional symbols fron `def_1`.
                current_stack_accumulated_symbols.clear()

                symbol_graph_upper_level = recurse_build(queue_symbol_def)

                # Accumulates successive bottom-upper stack level symbol graph builds.
                if current_stack_accumulated_symbol_graph:
                    from_upper_stack_to_accumulate_symbol_graph = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        current_stack_accumulated_symbol_graph,
                        from_upper_stack_to_accumulate_symbol_graph,
                    )
                else:
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )

                # Avoids leaving the the `lower` level stack after terminating a `higher` level stack.
                if bool(queue_symbol_def):
                    continue

                # We need to return at the last delimiter to not pop from an empty queue,
                # the expression needs to be correct syntactically.
                return current_stack_accumulated_symbol_graph

            if str_symbol in (")", "]", "}"):
                if str_symbol == ")":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.STANDARD
                elif str_symbol == "}":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.NONE_ANY
                elif str_symbol == "]":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.NONE_ONCE

                # Handles the case where there exist no opening `("(", "[", "{")` delimiter next to '|.
                # Example: (_1 `def_1` {_2 `def_2` 2_} `def_4` | `def_3` 1_), with `def_4` which could be empty.
                # In such case, we'll return the union of the left definition (`def_1` {`def_2`} `def_4`) to the `|`
                # with the right definition (`def_3`).
                if "|" in current_stack_accumulated_symbols:
                    index = current_stack_accumulated_symbols.index("|")
                    symbol_graph_or_lhs, symbol_graph_or_rhs = (
                        construct_symbol_subgraph(
                            current_stack_accumulated_symbols[:index]
                        ),
                        construct_symbol_subgraph(
                            current_stack_accumulated_symbols[index + 1 :]
                        ),
                    )
                    # Accumulate the left symbol graph with left portion before the '|' symbol.
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        current_stack_accumulated_symbol_graph, symbol_graph_or_lhs
                    )
                    # Union the left symbol graph with the right portion after the '|' symbol.
                    symbol_graph_out = union_symbol_graph(
                        current_stack_accumulated_symbol_graph, symbol_graph_or_rhs
                    )
                    return cast_symbol_graph(symbol_graph_out, SYMBOL_GRAPH_TYPE)

                current_stack_to_accumulate_symbol_graph = construct_symbol_subgraph(
                    current_stack_accumulated_symbols
                )
                symbol_graph_out = connect_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    current_stack_to_accumulate_symbol_graph,
                )
                return cast_symbol_graph(symbol_graph_out, SYMBOL_GRAPH_TYPE)

            elif str_symbol == "|":
                # Handles the case where there exist no opening `("(", "[", "{")` delimiter next to '|.
                if queue_symbol_def[0] not in ["(", "[", "{"]:
                    current_stack_accumulated_symbols.append(str_symbol)
                    continue

                # Handles the case where there exist an opening `("(", "[", "{")` delimiter next to '|.
                # Creates subgraph of accumulated symbols, if they exist; else return an empty graph.
                current_stack_to_accumulate_symbol_graph = construct_symbol_subgraph(
                    current_stack_accumulated_symbols
                )

                # Consumes `current_stack_accumulated_symbols.`
                current_stack_accumulated_symbols.clear()

                # Accumulates `current_stack_accumulated_symbol_graph`.
                current_stack_accumulated_symbol_graph = connect_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    current_stack_to_accumulate_symbol_graph,
                )

                # Avoids opening an additional stack.
                # One when encountering the symbol `|` and second with an opening delimiter (`(`, `[`, `{`).
                # Not doing so will (steal) an enclosing delimiter, thus breaking the logic.
                if queue_symbol_def[0] in ["(", "[", "{"]:
                    queue_symbol_def.popleft()

                from_upper_stack_to_accumulate_symbol_graph = recurse_build(
                    queue_symbol_def
                )

                current_stack_accumulated_symbol_graph = union_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    from_upper_stack_to_accumulate_symbol_graph,
                )

                if bool(queue_symbol_def):
                    continue

                return current_stack_accumulated_symbol_graph

            current_stack_accumulated_symbols.append(str_symbol)

    return recurse_build(queue_symbol_def)

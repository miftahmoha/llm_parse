from collections import defaultdict

import pytest

from cfg_parse.base import OrderedSet, Symbol, SymbolGraph
from cfg_parse.cfg_build.build import (
    build_symbol_graph,
    connect_symbol_graph,
    construct_symbol_subgraph,
)
from cfg_parse.cfg_build.helpers import get_symbols_from_generated_symbol_graph

# ----------------------------- construct_symbol_subgraph -----------------------------


@pytest.fixture
def simple_subdef_without_or():
    return """ "(" expression ")" """


def test_construct_symbol_subgraph_simple_subdef_without_or(
    simple_subdef_without_or: str,
):
    generated_symbol_graph = construct_symbol_subgraph(simple_subdef_without_or.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes = defaultdict(
        OrderedSet[Symbol],
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def simple_subdef_with_or():
    return """ factor "+" | factor "-" """


def test_construct_symbol_subgraph_simple_subdef_with_or(simple_subdef_with_or: str):
    # generated_symbol_graph = construct_symbol_subgraph(simple_subdef_with_or.split())
    generated_symbol_graph = build_symbol_graph(simple_subdef_with_or)
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols["factor|0"], symbols["factor|1"]])
    nodes = defaultdict(
        OrderedSet[Symbol],
        {
            symbols["factor|0"]: OrderedSet([symbols['"+"|0']]),
            symbols["factor|1"]: OrderedSet([symbols['"-"|0']]),
        },
    )
    finals = OrderedSet([symbols['"+"|0'], symbols['"-"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def simple_subdef_with_regex():
    return """ Regex([0-9]*.[0-9]*) """


def test_construct_symbol_subgraph_simple_subdef_with_regex(
    simple_subdef_with_regex: str,
):
    generated_symbol_graph = construct_symbol_subgraph(simple_subdef_with_regex.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols["[0-9]*.[0-9]*|0"]])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([]),
        },
    )
    finals = OrderedSet([symbols["[0-9]*.[0-9]*|0"]])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def subdef_with_regex_and_or():
    return """ Regex([0-9]*.[0-9]*) | "-" factor |  "(" expression ")" """


def test_construct_symbol_subgraph_subdef_with_regex_and_or(
    subdef_with_regex_and_or: str,
):
    generated_symbol_graph = build_symbol_graph(subdef_with_regex_and_or)
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet(
        [
            symbols["[0-9]*.[0-9]*|0"],
            symbols['"-"|0'],
            symbols['"("|0'],
        ]
    )
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"]]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet(
        [
            symbols["[0-9]*.[0-9]*|0"],
            symbols["factor|0"],
            symbols['")"|0'],
        ]
    )

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# ----------------------------- connect_symbol_graph -----------------------------


def test_connect_symbol_graph_simple_subdefs(
    simple_subdef_without_or: str, simple_subdef_with_regex: str
):
    symbol_sink_graph = construct_symbol_subgraph(simple_subdef_without_or.split())
    symbol_source_graph = construct_symbol_subgraph(simple_subdef_with_regex.split())
    generated_symbol_graph = connect_symbol_graph(
        symbol_sink_graph, symbol_source_graph
    )

    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols['")"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
        },
    )
    finals = OrderedSet([symbols["[0-9]*.[0-9]*|0"]])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)
    assert true_symbol_graph == generated_symbol_graph


def test_connect_symbol_graph_simple_subdefs_with_or(
    simple_subdef_without_or: str, simple_subdef_with_or: str
):
    symbol_graph_lhs = construct_symbol_subgraph(simple_subdef_with_or.split())
    symbol_graph_rhs = construct_symbol_subgraph(simple_subdef_without_or.split())
    generated_symbol_graph = connect_symbol_graph(symbol_graph_lhs, symbol_graph_rhs)
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols["factor|0"], symbols["factor|1"]])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols["factor|0"]: OrderedSet([symbols['"+"|0']]),
            symbols["factor|1"]: OrderedSet([symbols['"-"|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols['"("|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"("|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# [NOTE] The unique identifier is only relevant if we've got a repeated symbol in a definition.
def test_connect_symbol_graph_subdefs_with_regex_and_or(
    simple_subdef_with_or: str, subdef_with_regex_and_or: str
):
    symbol_graph_left = construct_symbol_subgraph(simple_subdef_with_or.split())
    symbol_graph_right = construct_symbol_subgraph(subdef_with_regex_and_or.split())
    generated_symbol_graph = connect_symbol_graph(symbol_graph_left, symbol_graph_right)
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols["factor|0"], symbols["factor|1"]])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols["factor|0"]: OrderedSet([symbols['"+"|0']]),
            symbols["factor|1"]: OrderedSet([symbols['"-"|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"-"|1'],
                    symbols['"("|0'],
                ]
            ),
            symbols['"-"|0']: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"-"|1'],
                    symbols['"("|0'],
                ]
            ),
            symbols['"-"|1']: OrderedSet(
                [
                    symbols["factor|2"],
                ]
            ),
        },
    )
    finals = OrderedSet(
        [
            symbols["[0-9]*.[0-9]*|0"],
            symbols["factor|2"],
            symbols['")"|0'],
        ]
    )

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_without_or_without_special_delimiters():
    return """ "(" expression (factor "-" Regex([0-9]*.[0-9]*)) ")" """


# ----------------------------- build_symbol_graph -----------------------------


# -------- SymbolGraphType.STANDARD --------


def test_build_graph_def_without_or_without_special_delimiters(
    def_without_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols["factor|0"]]),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_without_or_seq_without_special_delimiters():
    return """ "(" expression (factor "-" Regex([0-9]*.[0-9]*) (power "+") (factor "*") ("/" number) power) ")" """


def test_build_graph_def_without_or_seq_without_special_delimiters(
    def_without_or_seq_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_seq_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols["factor|0"]]),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols['"+"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['"*"|0']]),
            symbols['"*"|0']: OrderedSet([symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["number|0"]]),
            symbols["number|0"]: OrderedSet([symbols["power|1"]]),
            symbols["power|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters():
    return """ "(" expression (factor "-" (power "+") (factor "*") ("/" number) power ("/" Regex([0-9]*.[0-9]*)) (factor "+") expression) ")" """


def test_build_graph_def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters(
    def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols["factor|0"]]),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols['"+"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['"*"|0']]),
            symbols['"*"|0']: OrderedSet([symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["number|0"]]),
            symbols["number|0"]: OrderedSet([symbols["power|1"]]),
            symbols["power|1"]: OrderedSet([symbols['"/"|1']]),
            symbols['"/"|1']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_with_out_or_without_special_delimiters(
    def_with_out_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_out_or_ext_without_special_delimiters():
    return """ "(" expression ((factor "-") | Regex([0-9]*.[0-9]*) "+" factor) ")" """


def test_build_graph_def_with_out_or_ext_without_special_delimiters(
    def_with_out_or_ext_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_ext_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['"+"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (Regex([0-9]*.[0-9]*) | "+")) ")" """


def test_build_graph_def_with_in_and_out_or_without_special_delimiters(
    def_with_in_and_out_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"], symbols['"+"|0']]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# test_build_graph_def_with_in_and_out_or_without_special_delimiters(
#     """ "(" expression ((factor "-") | (Regex([0-9]*.[0-9]*) | "+")) ")" """
# )


@pytest.fixture
def def_with_in_and_out_ext_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (Regex([0-9]*.[0-9]*) factor | "+" expression)) ")" """


def test_build_graph_def_with_in_and_out_ext_or_without_special_delimiters(
    def_with_in_and_out_ext_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"], symbols['"+"|0']]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.NONE_ANY --------


@pytest.fixture
def def_without_or_with_special_delimiters_none_any():
    return """ "(" expression {factor "-" Regex([0-9]*.[0-9]*)} ")" """


def test_build_graph_def_with_or_with_special_delimiters_none_any(
    def_without_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)
    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["EOS_TOKEN|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet(
                [symbols["factor|0"], symbols['")"|0']]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ANY --------


@pytest.fixture
def def_with_out_or_with_special_delimiters_none_any():
    return """ "(" expression ({factor "-"} | Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_with_out_or_with_special_delimiters(
    def_with_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
        },
    )

    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_none_any():
    return """ "(" expression ({factor "-"} | {Regex([0-9]*.[0-9]*) | "+"}) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_none_any(
    def_with_in_and_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet(
                [symbols["[0-9]*.[0-9]*|0"], symbols['"+"|0'], symbols['")"|0']]
            ),
            symbols['"+"|0']: OrderedSet(
                [symbols["[0-9]*.[0-9]*|0"], symbols['"+"|0'], symbols['")"|0']]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_with_special_delimiters_none_any():
    return """ "(" expression {(factor "-") | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """


def test_build_graph_def_with_in_and_out_ext_or_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["EOS_TOKEN|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any():
    return """ "(" expression {(factor "-") ("+" power) | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """


# [NOTE] DFS visits the second `+` symbol from the subdefinition ("+" expression`) first. That is because
# the second symbol `+` is directly connected to the subgraph ("(" expression), while the first is deeper into
# the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["EOS_TOKEN|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any():
    return """ "(" expression {{factor "-"} ("+" power) | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """


# [NOTE] DFS visits the second `+` symbol from the subdefinition ("+" expression`) first. That is because
# the second symbol `+` is directly connected to the subgraph ("(" expression), while the first is deeper into
# the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any():
    return """ "(" expression {{factor "-"} ("/" factor) ("+" power) expression | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """


# [NOTE] DFS visits the third `expression` symbol from the subdefinition ("+" expression`) second and not third.
# That is because the third `expression` is higher in the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols["expression|2"]]),
            symbols["expression|2"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any():
    return """ "(" expression {{factor "-"} ("/" factor) {"+" power} expression (Regex([0-9]*.[0-9]*) "*") | {Regex([0-9]*.[0-9]*) factor | "+" expression}} ")" """


# [NOTE] DFS visits the third `expression` symbol from the subdefinition ("+" expression`) second and not third.
# That is because the third `expression` is higher in the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1'], symbols["EOS_TOKEN|1"]]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols['"+"|1'], symbols["expression|2"]]),
            symbols["expression|2"]: OrderedSet([symbols["[0-9]*.[0-9]*|1"]]),
            symbols["[0-9]*.[0-9]*|1"]: OrderedSet([symbols['"*"|0']]),
            symbols['"*"|0']: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.NONE_ONE --------


@pytest.fixture
def def_without_or_with_special_delimiters_none_once():
    return """ "(" expression [factor "-" Regex([0-9]*.[0-9]*)] ")" """


def test_build_graph_def_without_or_with_special_delimiters_none_once(
    def_without_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["EOS_TOKEN|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ONE --------


@pytest.fixture
def def_with_out_or_with_special_delimiters_none_once():
    return """ "(" expression ([factor "-"] | Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_with_out_or_with_special_delimiters_none_once(
    def_with_out_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_none_once():
    return """ "(" expression ([factor "-"] | [Regex([0-9]*.[0-9]*) | "+"]) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_none_once(
    def_with_in_and_out_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_with_special_delimiters_none_once():
    return """ "(" expression [(factor "-") | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """


def test_build_graph_def_with_in_and_out_ext_or_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["EOS_TOKEN|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once():
    return """ "(" expression [(factor "-") ("+" power) | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """


# [NOTE] DFS visits the second `+` symbol from the subdefinition ("+" expression`) first. That is because
# the second symbol `+` is directly connected to the subgraph ("(" expression), while the first is deeper into
# the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols["EOS_TOKEN|0"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once():
    return """ "(" expression [[factor "-"] ("+" power) | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """


# [NOTE] DFS visits the second `+` symbol from the subdefinition ("+" expression`) first. That is because
# the second symbol `+` is directly connected to the subgraph ("(" expression), while the first is deeper into
# the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once():
    return """ "(" expression [[factor "-"] ("/" factor) ("+" power) expression | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """


# [NOTE] DFS visits the third `expression` symbol from the subdefinition ("+" expression`) second and not third.
# That is because the third `expression` is higher in the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1']]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols["expression|2"]]),
            symbols["expression|2"]: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once(
#     """ "(" expression [[factor "-"] ("/" factor) ("+" power) expression | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """
# )


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once():
    return """ "(" expression [[factor "-"] ("/" factor) ["+" power] expression (Regex([0-9]*.[0-9]*) "*") | [Regex([0-9]*.[0-9]*) factor | "+" expression]] ")" """


# [NOTE] DFS visits the third `expression` symbol from the subdefinition ("+" expression`) second and not third.
# That is because the third `expression` is higher in the tree.
def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1'], symbols["EOS_TOKEN|1"]]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols["expression|2"]]),
            symbols["expression|2"]: OrderedSet([symbols["[0-9]*.[0-9]*|1"]]),
            symbols["[0-9]*.[0-9]*|1"]: OrderedSet([symbols['"*"|0']]),
            symbols['"*"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet([symbols['")"|0']]),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ANY + SymbolGraphType.NONE_ONE --------


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once():
    return """ "(" expression {{factor "-"} ("/" factor) ["+" power] expression (Regex([0-9]*.[0-9]*) "*") | [Regex([0-9]*.[0-9]*) factor | "+" expression]} ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    initials = OrderedSet([symbols['"("|0']])
    nodes: dict[Symbol, OrderedSet] = dict(
        {
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['"/"|0']]),
            symbols['"/"|0']: OrderedSet([symbols["factor|2"]]),
            symbols["factor|2"]: OrderedSet([symbols['"+"|1'], symbols["EOS_TOKEN|1"]]),
            symbols['"+"|1']: OrderedSet([symbols["power|0"]]),
            symbols["power|0"]: OrderedSet([symbols["expression|2"]]),
            symbols["expression|2"]: OrderedSet([symbols["[0-9]*.[0-9]*|1"]]),
            symbols["[0-9]*.[0-9]*|1"]: OrderedSet([symbols['"*"|0']]),
            symbols['"*"|0']: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
            symbols['"+"|0']: OrderedSet([symbols["expression|1"]]),
            symbols["expression|1"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"+"|0'],
                    symbols['")"|0'],
                ]
            ),
        },
    )
    finals = OrderedSet([symbols['")"|0']])

    true_symbol_graph = SymbolGraph(initials=initials, nodes=nodes, finals=finals)

    assert true_symbol_graph == generated_symbol_graph

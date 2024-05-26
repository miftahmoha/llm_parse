from collections import defaultdict, deque
from copy import deepcopy
from networkx import draw

import pytest

from cfg_parser import (
    construct_symbol_subgraph,
    connect_symbol_graph,
    build_symbol_graph,
)
from cfg_parser.base import OrderedSet, Symbol
from cfg_parser.functions import (
    get_symbols_from_generated_symbol_graph,
)
from cfg_parser.draw import draw_symbol_graph


@pytest.fixture
def simple_subdef_without_or():
    return """ "(" expression ")" """


def test_construct_symbol_subgraph_simple_subdef_without_or(
    simple_subdef_without_or: str,
):
    generated_symbol_graph = construct_symbol_subgraph(simple_subdef_without_or.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    true_symbol_graph = defaultdict(
        OrderedSet[Symbol],
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def simple_subdef_with_or():
    return """ factor "+" | factor "-" """


def test_construct_symbol_subgraph_simple_subdef_with_or(simple_subdef_with_or: str):
    generated_symbol_graph = construct_symbol_subgraph(simple_subdef_with_or.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    true_symbol_graph = defaultdict(
        OrderedSet[Symbol],
        {
            symbols["SOURCE"]: OrderedSet([symbols["factor|0"], symbols["factor|1"]]),
            symbols["factor|0"]: OrderedSet([symbols['"+"|0']]),
            symbols["factor|1"]: OrderedSet([symbols['"-"|0']]),
            symbols["SINK"]: OrderedSet([symbols['"+"|0'], symbols['"-"|0']]),
        },
    )

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def simple_subdef_with_regex():
    return """ Regex([0-9]*.[0-9]*) """


def test_construct_symbol_subgraph_simple_subdef_with_regex(
    simple_subdef_with_regex: str,
):
    generated_symbol_graph = construct_symbol_subgraph(simple_subdef_with_regex.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    true_symbol_graph = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["SINK"]: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
        },
    )

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def subdef_with_regex_and_or():
    return """ Regex([0-9]*.[0-9]*) | "-" factor |  "(" expression ")" """


def test_construct_symbol_subgraph_subdef_with_regex_and_or(
    subdef_with_regex_and_or: str,
):
    generated_symbol_graph = construct_symbol_subgraph(subdef_with_regex_and_or.split())
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    true_symbol_graph = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols['"-"|0'],
                    symbols['"("|0'],
                ]
            ),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"]]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols["factor|0"],
                    symbols['")"|0'],
                ]
            ),
        },
    )

    assert true_symbol_graph == generated_symbol_graph


def test_connect_symbol_graph_simple_subdefs(
    simple_subdef_without_or: str, simple_subdef_with_regex: str
):
    symbol_sink_graph = construct_symbol_subgraph(simple_subdef_without_or.split())
    symbol_source_graph = construct_symbol_subgraph(simple_subdef_with_regex.split())
    generated_symbol_graph = connect_symbol_graph(
        symbol_sink_graph, symbol_source_graph
    )

    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph)

    true_symbol_graph = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols['")"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["SINK"]: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
        },
    )

    assert true_symbol_graph == generated_symbol_graph


def test_connect_symbol_graph_simple_subdefs_with_or(
    simple_subdef_without_or: str, simple_subdef_with_or: str
):
    symbol_sink_graph = construct_symbol_subgraph(simple_subdef_with_or.split())
    symbol_source_graph = construct_symbol_subgraph(simple_subdef_without_or.split())
    generated_symbol_graph_output = connect_symbol_graph(
        symbol_sink_graph, symbol_source_graph
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols["factor|0"], symbols["factor|1"]]),
            symbols["factor|0"]: OrderedSet([symbols['"+"|0']]),
            symbols["factor|1"]: OrderedSet([symbols['"-"|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols['"("|0']]),
            symbols['"-"|0']: OrderedSet([symbols['"("|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


# [NOTE] The unique identifier is only relevant if we've got a repeated symbol in a definition.
def test_connect_symbol_graph_subdefs_with_regex_and_or(
    simple_subdef_with_or: str, subdef_with_regex_and_or: str
):
    symbol_graph_left = construct_symbol_subgraph(simple_subdef_with_or.split())
    symbol_graph_right = construct_symbol_subgraph(subdef_with_regex_and_or.split())
    generated_symbol_graph_output = connect_symbol_graph(
        symbol_graph_left, symbol_graph_right
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols["factor|0"], symbols["factor|1"]]),
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
            symbols["SINK"]: OrderedSet(
                [
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols["factor|2"],
                    symbols['")"|0'],
                ]
            ),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_without_or_without_special_delimiters():
    return """ "(" expression (factor "-" Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_without_or_without_special_delimiters(
    def_without_or_without_special_delimiters: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_without_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet([symbols["factor|0"]]),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_with_out_or_without_special_delimiters(
    def_with_out_or_without_special_delimiters: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_out_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_out_or_ext_without_special_delimiters():
    return """ "(" expression ((factor "-") | Regex([0-9]*.[0-9]*) "+" factor) ")" """


def test_build_graph_def_with_out_or_ext_without_special_delimiters(
    def_with_out_or_ext_without_special_delimiters: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_out_or_ext_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['"+"|0']]),
            symbols['"+"|0']: OrderedSet([symbols["factor|1"]]),
            symbols["factor|1"]: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_in_and_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (Regex([0-9]*.[0-9]*) | "+")) ")" """


def test_build_graph_def_with_in_and_out_or_without_special_delimiters(
    def_with_in_and_out_or_without_special_delimiters: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_in_and_out_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"], symbols['"+"|0']]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet([symbols['")"|0']]),
            symbols['"+"|0']: OrderedSet([symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_in_and_out_ext_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (Regex([0-9]*.[0-9]*) factor | "+" expression)) ")" """


def test_build_graph_def_with_in_and_out_ext_or_without_special_delimiters(
    def_with_in_and_out_ext_or_without_special_delimiters: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_in_and_out_ext_or_without_special_delimiters
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
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
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_without_or_with_special_delimiters_none_any():
    return """ "(" expression {factor "-" Regex([0-9]*.[0-9]*)} ")" """


def test_build_graph_def_with_or_with_special_delimiters_none_any(
    def_without_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_without_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [symbols["factor|0"], symbols["EOS_TOKEN|0"]]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["[0-9]*.[0-9]*|0"]]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet(
                [symbols["factor|0"], symbols['")"|0']]
            ),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_out_or_with_special_delimiters_none_any():
    return """ "(" expression ({factor "-"} | Regex([0-9]*.[0-9]*)) ")" """


def test_build_graph_def_with_out_or_with_special_delimiters(
    def_with_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_out_or_with_special_delimiters_none_any
    )
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
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
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_none_any():
    return """ "(" expression ({factor "-"} | {Regex([0-9]*.[0-9]*) | "+"}) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_none_any(
    def_with_in_and_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph_output = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_none_any
    )
    draw_symbol_graph(generated_symbol_graph_output)
    symbols = get_symbols_from_generated_symbol_graph(generated_symbol_graph_output)

    true_symbol_graph_output = defaultdict(
        OrderedSet,
        {
            symbols["SOURCE"]: OrderedSet([symbols['"("|0']]),
            symbols['"("|0']: OrderedSet([symbols["expression|0"]]),
            symbols["expression|0"]: OrderedSet(
                [
                    symbols["factor|0"],
                    symbols["EOS_TOKEN|0"],
                    symbols["[0-9]*.[0-9]*|0"],
                    symbols["EOS_TOKEN|1"],
                    symbols['"+"|0'],
                    symbols["EOS_TOKEN|2"],
                ]
            ),
            symbols["factor|0"]: OrderedSet([symbols['"-"|0']]),
            symbols['"-"|0']: OrderedSet([symbols["factor|0"], symbols['")"|0']]),
            symbols["[0-9]*.[0-9]*|0"]: OrderedSet(
                [symbols["[0-9]*.[0-9]*|0"], symbols['")"|0']]
            ),
            symbols['"+"|0']: OrderedSet([symbols['"+"|0'], symbols['")"|0']]),
            symbols["SINK"]: OrderedSet([symbols['")"|0']]),
        },
    )

    assert true_symbol_graph_output == generated_symbol_graph_output

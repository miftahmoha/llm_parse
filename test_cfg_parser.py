from collections import defaultdict

import pytest

from cfg_parser import Symbol, SymbolType, construct_symbol_graph, connect_symbol_graph
from cfg_parser.cfg_parser import connect_symbol_graph

@pytest.fixture
def simple_def_without_or():
    return ''' "(" expression ")" ''' 

def test_construct_symbol_graph_simple_def_without_or(simple_def_without_or: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            '"("': Symbol('"("', SymbolType.TERMINAL),
            'expression': Symbol('expression', SymbolType.NOT_TERMINAL),
            '")"': Symbol('")"', SymbolType.TERMINAL),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }
    true_symbol_graph = defaultdict(
        set,
        {symbols['SOURCE']: {symbols['"("']}, symbols['"("']: {symbols['expression']}, symbols['expression']: {symbols['")"']}, symbols['SINK']: {symbols['")"']}},
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_without_or)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def simple_def_with_or():
    return ''' factor "+" | factor "-" '''

def test_construct_symbol_graph_simple_def_with_or(simple_def_with_or: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            'factor': Symbol('factor', SymbolType.NOT_TERMINAL),
            '"+"': Symbol('"+"', SymbolType.TERMINAL),
            '"-"': Symbol('"-"', SymbolType.TERMINAL),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }

    true_symbol_graph = defaultdict(
        set,
        {symbols['SOURCE']: {symbols['factor']}, symbols['factor']: {symbols['"+"'], symbols['"-"']}, symbols['SINK']: {symbols['"+"'], symbols['"-"']}}, 
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_with_or)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def simple_def_with_regex():
    return ''' Regex([0-9]*.[0-9]*) '''

def test_construct_symbol_graph_simple_def_with_regex(simple_def_with_regex: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            'Regex([0-9]*.[0-9]*)': Symbol('[0-9]*.[0-9]*', SymbolType.REGEX),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }

    true_symbol_graph = defaultdict(
        set,
        {symbols['SOURCE']: {symbols['Regex([0-9]*.[0-9]*)']}, symbols['SINK']: {symbols['Regex([0-9]*.[0-9]*)']}}
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_with_regex)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def def_with_regex_and_or():
    return ''' Regex([0-9]*.[0-9]*) | "-" factor |  "(" expression ")" '''


def test_construct_symbol_graph_def_with_regex_and_or(def_with_regex_and_or: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            'Regex([0-9]*.[0-9]*)': Symbol('[0-9]*.[0-9]*', SymbolType.REGEX),
            '"-"': Symbol('"-"', SymbolType.TERMINAL),
            'factor': Symbol('factor', SymbolType.NOT_TERMINAL),
            '"("': Symbol('"("', SymbolType.TERMINAL),
            'expression': Symbol('expression', SymbolType.NOT_TERMINAL),
            '")"': Symbol('")"', SymbolType.TERMINAL),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }

    true_symbol_graph = defaultdict(
        set,
        {symbols['SOURCE']: {symbols['Regex([0-9]*.[0-9]*)'], symbols['"-"'], symbols['"("']}, symbols['"-"']: {symbols['factor']}, symbols['"("']: {symbols['expression']}, symbols['expression']: {symbols['")"']}, symbols['SINK']: {symbols['Regex([0-9]*.[0-9]*)'], symbols['factor'], symbols['")"']}}, 
    )
    generated_symbol_graph = construct_symbol_graph(def_with_regex_and_or)

    assert true_symbol_graph == generated_symbol_graph

def test_connect_symbol_graph_simple_defs(simple_def_without_or: str, simple_def_with_regex: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            '"("': Symbol('"("', SymbolType.TERMINAL),
            'expression': Symbol('expression', SymbolType.NOT_TERMINAL),
            '")"': Symbol('")"', SymbolType.TERMINAL),
            'Regex([0-9]*.[0-9]*)': Symbol('[0-9]*.[0-9]*', SymbolType.REGEX),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }

    true_symbol_graph_output = defaultdict(set, 
        {symbols['SOURCE']: {symbols['"("']}, symbols['"("']: {symbols['expression']}, symbols['expression']: {symbols['")"']}, symbols['")"']: {symbols['Regex([0-9]*.[0-9]*)']}, symbols['SINK']: {symbols['Regex([0-9]*.[0-9]*)']}})

    symbol_sink_graph = construct_symbol_graph(simple_def_without_or)
    symbol_source_graph = construct_symbol_graph(simple_def_with_regex)
    generated_symbol_graph_output = connect_symbol_graph(symbol_sink_graph, symbol_source_graph)

    assert true_symbol_graph_output == generated_symbol_graph_output


def test_connect_symbol_graph_simple_defs_with_or(simple_def_without_or: str, simple_def_with_or: str):
    symbols = {
            'SOURCE': Symbol('SOURCE', SymbolType.NOT_TERMINAL),
            'factor': Symbol('factor', SymbolType.NOT_TERMINAL),
            '"+"': Symbol('"+"', SymbolType.TERMINAL),
            '"-"': Symbol('"-"', SymbolType.TERMINAL),
            '"("': Symbol('"("', SymbolType.TERMINAL),
            'expression': Symbol('expression', SymbolType.NOT_TERMINAL),
            '")"': Symbol('")"', SymbolType.TERMINAL),
            'SINK': Symbol('SINK', SymbolType.NOT_TERMINAL),
    }

    true_symbol_graph_output = defaultdict(set, 
            {symbols['SOURCE']: {symbols['factor']}, symbols['factor']: {symbols['"+"'], symbols['"-"']}, symbols['"("']: {symbols['expression']}, symbols['expression']: {symbols['")"']}, symbols['"+"']: {symbols['"("']}, symbols['"-"']: {symbols['"("']}, symbols['SINK']: {symbols['")"']}}) 

    symbol_sink_graph = construct_symbol_graph(simple_def_with_or)
    symbol_source_graph = construct_symbol_graph(simple_def_without_or)
    generated_symbol_graph_output = connect_symbol_graph(symbol_sink_graph, symbol_source_graph)

    assert true_symbol_graph_output == generated_symbol_graph_output

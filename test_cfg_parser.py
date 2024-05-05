from collections import defaultdict

import pytest

from cfg_parser import Symbol, SymbolType, construct_symbol_graph

@pytest.fixture
def simple_def_without_or():
    return ''' "(" expression ")" ''' 

def test_construct_simple_def_without_or(simple_def_without_or: str):
    symbols = [
        Symbol('ROOTS', SymbolType.NOT_TERMINAL),
        Symbol('"("', SymbolType.TERMINAL),
        Symbol('expression', SymbolType.NOT_TERMINAL),
        Symbol('")"', SymbolType.TERMINAL),
    ]
    true_symbol_graph = defaultdict(
        list,
        {symbols[0]: {symbols[1]}, symbols[1]: {symbols[2]}, symbols[2]: {symbols[3]}},
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_without_or)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def simple_def_with_or():
    return ''' factor "+" | factor "-" '''

def test_construct_simple_def_with_or(simple_def_with_or: str):
    symbols = [
        Symbol('ROOTS', SymbolType.NOT_TERMINAL),
        Symbol('factor', SymbolType.NOT_TERMINAL),
        Symbol('"+"', SymbolType.TERMINAL),
        Symbol('"-"', SymbolType.TERMINAL),
    ]

    true_symbol_graph = defaultdict(
        set,
        {symbols[0]: {symbols[1]}, symbols[1]: {symbols[2], symbols[3]}},
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_with_or)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def simple_def_with_regex():
    return ''' Regex([0-9]*.[0-9]*) '''

def test_construct_simple_def_with_regex(simple_def_with_regex: str):
    symbols = [
        Symbol('ROOTS', SymbolType.NOT_TERMINAL),
        Symbol('[0-9]*.[0-9]*', SymbolType.REGEX)
    ]

    true_symbol_graph = defaultdict(
        set,
        {symbols[0]: {symbols[1]}},
    )
    generated_symbol_graph = construct_symbol_graph(simple_def_with_regex)

    assert true_symbol_graph == generated_symbol_graph

@pytest.fixture
def def_with_regex_and_or():
    return ''' Regex([0-9]*.[0-9]*) | "-" factor |  "(" expression ")" '''


def test_construct_def_with_regex_and_or(def_with_regex_and_or: str):
    symbols = [
        Symbol('ROOTS', SymbolType.NOT_TERMINAL),
        Symbol('[0-9]*.[0-9]*', SymbolType.REGEX),
        Symbol('"-"', SymbolType.TERMINAL),
        Symbol('factor', SymbolType.NOT_TERMINAL),
        Symbol('"("', SymbolType.TERMINAL),
        Symbol('expression', SymbolType.NOT_TERMINAL),
        Symbol('")"', SymbolType.TERMINAL),
    ]

    true_symbol_graph = defaultdict(
        set,
        {symbols[0]: {symbols[1], symbols[2], symbols[4]}, symbols[2]: {symbols[3]}, symbols[4]: {symbols[5]}, symbols[5]:{symbols[6]}},
    )
    generated_symbol_graph = construct_symbol_graph(def_with_regex_and_or)

    assert true_symbol_graph == generated_symbol_graph

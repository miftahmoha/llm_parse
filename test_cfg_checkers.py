import pytest

from cfg_parse.cfg_build.build import _convert_str_def_to_str_queue

from cfg_parse.cfg_guide.guide import _divide_cfg_grammar_into_definitions


from cfg_parse.exceptions import InvalidDelimiters, InvalidGrammar, InvalidSymbol

# ----------------------------- InvalidSymbol -----------------------------


@pytest.fixture
def invalid_symbol_terminal_missing_left_quotation():
    return """ Regex("[0-9]*.[0-9]*") | -" factor |  "(" expression ")" """


def test_invalid_symbol_regex_missing_left_quotation(
    invalid_symbol_terminal_missing_left_quotation: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(invalid_symbol_terminal_missing_left_quotation)

    assert str(exc_info.value) == f'Invalid symbol name -".'


@pytest.fixture
def invalid_symbol_terminal_missing_right_quotation():
    return """ Regex("[0-9]*.[0-9]*") | "- factor |  "(" expression ")" """


def test_invalid_symbol_terminal_missing_right_quotation(
    invalid_symbol_terminal_missing_right_quotation: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(invalid_symbol_terminal_missing_right_quotation)

    assert str(exc_info.value) == f'Invalid symbol name "-.'


@pytest.fixture
def invalid_symbol_regex_missing_left_quotation():
    return """ Regex([0-9]*.[0-9]*") | "-" fact@or |  "(" expression ")" """


def test_invalid_symbol_regex_missing_left_quotation(
    invalid_symbol_regex_missing_left_quotation: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(invalid_symbol_regex_missing_left_quotation)

    assert str(exc_info.value) == f'Invalid symbol name Regex([0-9]*.[0-9]*").'


@pytest.fixture
def invalid_symbol_regex_missing_right_quotation():
    return """ Regex("[0-9]*.[0-9]*) | "-" fact@or |  "(" expression ")" """


def test_invalid_symbol_regex_missing_right_quotation(
    invalid_symbol_regex_missing_right_quotation: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(invalid_symbol_regex_missing_right_quotation)

    assert str(exc_info.value) == f'Invalid symbol name Regex("[0-9]*.[0-9]*).'


@pytest.fixture
def invalid_symbol_non_terminal_with_special_characters_0x40():
    return """ Regex("[0-9]*.[0-9]*") | "-" fact@or |  "(" expression ")" """


def test_invalid_symbol_non_terminal_with_special_characters_0x40(
    invalid_symbol_non_terminal_with_special_characters_0x40: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(
            invalid_symbol_non_terminal_with_special_characters_0x40
        )

    assert str(exc_info.value) == f"Invalid symbol name fact@or."


@pytest.fixture
def invalid_symbol_non_terminal_with_special_characters_0x2F():
    return """ Regex("[0-9]*.[0-9]*") | "-" factor |  "(" expre/ssion ")" """


def test_invalid_symbol_non_terminal_with_special_characters_0x2F(
    invalid_symbol_non_terminal_with_special_characters_0x2F: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(
            invalid_symbol_non_terminal_with_special_characters_0x2F
        )

    assert str(exc_info.value) == f"Invalid symbol name expre/ssion."


@pytest.fixture
def invalid_symbol_non_terminal_with_special_characters_0x5E():
    return """ Regex("[0-9]*.[0-9]*") | "-" factor |  "(" expressi^on ")" """


def test_invalid_symbol_non_terminal_with_special_characters_0x5E(
    invalid_symbol_non_terminal_with_special_characters_0x5E: str,
):
    with pytest.raises(InvalidSymbol) as exc_info:
        _convert_str_def_to_str_queue(
            invalid_symbol_non_terminal_with_special_characters_0x5E
        )

    assert str(exc_info.value) == f"Invalid symbol name expressi^on."


# ----------------------------- InvalidDelimiters -----------------------------


@pytest.fixture
def invalid_delimiters_missing_without_special_delimiters():
    return """ "(" expression (factor "-" Regex("[0-9]*.[0-9]*") ")" """


def test_invalid_delimiters_missing_without_special_delimiters(
    invalid_delimiters_missing_without_special_delimiters: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(
            invalid_delimiters_missing_without_special_delimiters
        )

    assert str(exc_info.value) == f"Non enclosed delimiter `(` in `(`."


@pytest.fixture
def invalid_delimiters_open_standard_close_none_any():
    return """ "(" expression (factor "-" Regex("[0-9]*.[0-9]*")} ")" """


def test_invalid_delimiters_open_standard_close_none_any(
    invalid_delimiters_open_standard_close_none_any: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_standard_close_none_any)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `{` found for `}` in `( "(" expression ( factor "-" Regex("[0-9]*.[0-9]*") <<}>>`.'
    )


@pytest.fixture
def invalid_delimiters_open_standard_close_none_once():
    return """ "(" expression (factor "-" Regex("[0-9]*.[0-9]*")] ")" """


def test_invalid_delimiters_open_standard_close_none_once(
    invalid_delimiters_open_standard_close_none_once: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_standard_close_none_once)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `[` found for `]` in `( "(" expression ( factor "-" Regex("[0-9]*.[0-9]*") <<]>>`.'
    )


@pytest.fixture
def invalid_delimiters_open_none_any_close_standard():
    return """ "(" expression {factor "-" Regex("[0-9]*.[0-9]*")) ")" """


def test_invalid_delimiters_open_none_any_close_standard(
    invalid_delimiters_open_none_any_close_standard: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_none_any_close_standard)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `(` found for `)` in `( "(" expression { factor "-" Regex("[0-9]*.[0-9]*") <<)>>`.'
    )


@pytest.fixture
def invalid_delimiters_open_none_once_close_standard():
    return """ "(" expression [factor "-" Regex("[0-9]*.[0-9]*")) ")" """


def test_invalid_delimiters_open_none_once_close_standard(
    invalid_delimiters_open_none_once_close_standard: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_none_once_close_standard)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `(` found for `)` in `( "(" expression [ factor "-" Regex("[0-9]*.[0-9]*") <<)>>`.'
    )


@pytest.fixture
def invalid_delimiters_open_none_any_close_none_once():
    return """ "(" expression {factor "-" Regex("[0-9]*.[0-9]*")] ")" """


def test_invalid_delimiters_open_none_any_close_none_once(
    invalid_delimiters_open_none_any_close_none_once: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_none_any_close_none_once)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `[` found for `]` in `( "(" expression [ factor "-" Regex("[0-9]*.[0-9]*") <<]>>`.'
    )


@pytest.fixture
def invalid_delimiters_open_none_once_close_none_any():
    return """ "(" expression [factor "-" Regex("[0-9]*.[0-9]*")} ")" """


def test_invalid_delimiters_open_none_any_close_none_once(
    invalid_delimiters_open_none_once_close_none_any: str,
):
    with pytest.raises(InvalidDelimiters) as exc_info:
        _convert_str_def_to_str_queue(invalid_delimiters_open_none_once_close_none_any)

    assert (
        str(exc_info.value)
        == 'No opening delimiter `{` found for `}` in `( "(" expression [ factor "-" Regex("[0-9]*.[0-9]*") <<}>>`.'
    )


# ----------------------------- InvalidGrammar -----------------------------
@pytest.fixture
def invalid_grammar_rule_name_0x40():
    return r"""
    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUM@BER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_rule_name_0x40(
    invalid_grammar_rule_name_0x40: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_rule_name_0x40)

    assert str(exc_info.value) == "Invalid rule name: NUM@BER."


@pytest.fixture
def invalid_grammar_rule_name_0x2F():
    return r"""
    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor}

    fact/or: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_rule_name_0x2F(
    invalid_grammar_rule_name_0x2F: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_rule_name_0x2F)

    assert str(exc_info.value) == "Invalid rule name: fact/or."


@pytest.fixture
def invalid_grammar_rule_name_0x5E():
    return r"""
    expression: term {("+" | "-") term}

    ter^m: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_rule_name_0x5E(
    invalid_grammar_rule_name_0x5E: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_rule_name_0x5E)

    assert str(exc_info.value) == "Invalid rule name: ter^m."


@pytest.fixture
def invalid_grammar_missing_start():
    return r"""
    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_missing_start(
    invalid_grammar_missing_start: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_missing_start)

    assert str(exc_info.value) == "The symbol `start` is non-existant."


@pytest.fixture
def invalid_grammar_redefinition():
    return r"""
    start: expression

    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"
    
    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_redefinition(
    invalid_grammar_redefinition: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_redefinition)

    assert str(exc_info.value) == "Redefinition of grammar rule: factor."


@pytest.fixture
def invalid_grammar_join_colons_multiple():
    return r"""
    start: expression

    expression: term {("+" | "-") term}

    term:: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_join_colons_multiple(
    invalid_grammar_join_colons_multiple: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_join_colons_multiple)

    assert (
        str(exc_info.value)
        == 'Invalid grammar rule: term:: factor {("*" | "/") factor}.'
    )


@pytest.fixture
def invalid_grammar_sepr_colons_multiple():
    return r"""
    start: expression

    expression: term {("+" | "-") term}

    term: factor {("*" | "/"): factor}

    factor: NUMBER
           | "-": factor
           | "(" expression ")"

    NUMBER: Regex("[0-9]+\.[0-9]+")
    """


def test_invalid_grammar_sepr_colons_multiple(
    invalid_grammar_sepr_colons_multiple: str,
):
    with pytest.raises(InvalidGrammar) as exc_info:
        _divide_cfg_grammar_into_definitions(invalid_grammar_sepr_colons_multiple)

    assert (
        str(exc_info.value)
        == 'Invalid grammar rule: term: factor {("*" | "/"): factor}.'
    )

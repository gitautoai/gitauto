from utils.number.is_valid_line_number import is_valid_line_number


def test_valid_integers():
    assert is_valid_line_number(2) is True
    assert is_valid_line_number(3) is True
    assert is_valid_line_number(100) is True


def test_invalid_integers():
    assert is_valid_line_number(0) is False
    assert is_valid_line_number(-1) is False
    assert is_valid_line_number(1) is False


def test_valid_strings():
    assert is_valid_line_number("2") is True
    assert is_valid_line_number("3") is True
    assert is_valid_line_number("100") is True


def test_invalid_strings():
    assert is_valid_line_number("0") is False
    assert is_valid_line_number("-1") is False
    assert is_valid_line_number("1") is False


def test_non_numeric_strings():
    assert is_valid_line_number("abc") is False
    assert is_valid_line_number("1.5") is False
    assert is_valid_line_number("1a") is False


def test_none_value():
    assert is_valid_line_number(None) is False


def test_boolean_values():
    assert is_valid_line_number(True) is False
    assert is_valid_line_number(False) is False


def test_float_values():
    assert is_valid_line_number(1.5) is False
    assert is_valid_line_number(2.0) is False
    assert is_valid_line_number(-1.5) is False


def test_empty_string():
    assert is_valid_line_number("") is False


def test_whitespace_string():
    assert is_valid_line_number(" ") is False
    assert is_valid_line_number("\t") is False
    assert is_valid_line_number("\n") is False


def test_complex_objects_trigger_exception_handler():
    class ComplexObject:
        def __str__(self):
            return "complex"

    obj = ComplexObject()
    assert str(obj) == "complex"
    assert is_valid_line_number(ComplexObject()) is False


def test_super_strict_failure_case():
    class ComplexObject:
        def __str__(self):
            raise ValueError("String conversion failed")

    obj = ComplexObject()
    try:
        str(obj)
        assert False, "Expected ValueError was not raised"
    except ValueError:
        pass
    assert is_valid_line_number(ComplexObject()) is False


def test_exception_during_processing():
    class BadObject:
        def __int__(self):
            raise ValueError("Cannot convert to int")

    obj = BadObject()
    try:
        int(obj)
        assert False, "Expected ValueError was not raised"
    except ValueError:
        pass
    assert is_valid_line_number(BadObject()) is False


def test_list_values():
    assert is_valid_line_number([]) is False
    assert is_valid_line_number([1, 2, 3]) is False
    assert is_valid_line_number(["1", "2", "3"]) is False


def test_dict_values():
    assert is_valid_line_number({}) is False
    assert is_valid_line_number({"line": 1}) is False


def test_scientific_notation_strings():
    assert is_valid_line_number("2e1") is False
    assert is_valid_line_number("1e2") is False
    assert is_valid_line_number("2E1") is False


def test_objects_with_custom_methods():
    class StringableObject:
        def __str__(self):
            return "2"

    class IntableObject:
        def __int__(self):
            return 2

    # Even though these objects can be converted to valid line numbers
    # through their custom methods, they're not valid input types
    # and should be caught by the exception handler
    assert is_valid_line_number(StringableObject()) is False
    assert is_valid_line_number(IntableObject()) is False


def test_objects_with_multiple_custom_methods():
    class ComplexNumberLike:
        def __str__(self):
            return "2"
        
        def __int__(self):
            return 2
    
    assert is_valid_line_number(ComplexNumberLike()) is False
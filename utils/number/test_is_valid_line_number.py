from utils.number.is_valid_line_number import is_valid_line_number


def test_valid_integer_line_numbers():
    assert is_valid_line_number(2) is True
    assert is_valid_line_number(10) is True
    assert is_valid_line_number(100) is True
    assert is_valid_line_number(999999) is True


def test_invalid_integer_line_numbers():
    assert is_valid_line_number(1) is False
    assert is_valid_line_number(0) is False
    assert is_valid_line_number(-1) is False
    assert is_valid_line_number(-100) is False


def test_valid_string_line_numbers():
    assert is_valid_line_number("2") is True
    assert is_valid_line_number("10") is True
    assert is_valid_line_number("100") is True
    assert is_valid_line_number("999999") is True


def test_invalid_string_line_numbers():
    assert is_valid_line_number("1") is False
    assert is_valid_line_number("0") is False
    assert is_valid_line_number("-1") is False
    assert is_valid_line_number("-100") is False


def test_non_digit_strings():
    assert is_valid_line_number("abc") is False
    assert is_valid_line_number("2.5") is False
    assert is_valid_line_number("2a") is False
    assert is_valid_line_number("a2") is False
    assert is_valid_line_number("") is False
    assert is_valid_line_number(" ") is False
    assert is_valid_line_number("  2  ") is False


def test_edge_case_strings():
    assert is_valid_line_number("00") is False
    assert is_valid_line_number("01") is False
    assert is_valid_line_number("02") is True


def test_invalid_types_trigger_exception_handler():
    assert is_valid_line_number(None) is False
    assert is_valid_line_number([]) is False
    assert is_valid_line_number({}) is False
    assert is_valid_line_number(2.5) is False
    assert is_valid_line_number(True) is False
    assert is_valid_line_number(False) is False


def test_complex_objects_trigger_exception_handler():
    class ComplexObject:
        def __str__(self):
            result = "complex"
            return result
    
    assert is_valid_line_number(ComplexObject()) is False


def test_super_strict_failure_case():
    class ComplexObject:
        def __str__(self):
            error_message = "String conversion failed"
            raise ValueError(error_message)
    
    assert is_valid_line_number(ComplexObject()) is False


def test_exception_during_processing():
    class BadObject:
        def __int__(self):
            error_message = "Cannot convert to int"
            raise ValueError(error_message)
    
    assert is_valid_line_number(BadObject()) is False


def test_large_numbers():
    assert is_valid_line_number(2**31) is True
    assert is_valid_line_number(str(2**31)) is True
    assert is_valid_line_number(2**63 - 1) is True


def test_boundary_values():
    assert is_valid_line_number(1) is False
    assert is_valid_line_number(2) is True
    assert is_valid_line_number("1") is False
    assert is_valid_line_number("2") is True


def test_unicode_and_special_characters():
    assert is_valid_line_number("２") is True
    assert is_valid_line_number("2️⃣") is False
    assert is_valid_line_number("②") is False
    assert is_valid_line_number("\n2\n") is False
    assert is_valid_line_number("\t2\t") is False


def test_very_long_strings():
    long_digit_string = "2" * 1000
    assert is_valid_line_number(long_digit_string) is True
    
    long_non_digit_string = "a" * 1000
    assert is_valid_line_number(long_non_digit_string) is False


def test_mixed_content_strings():
    assert is_valid_line_number("2abc") is False
    assert is_valid_line_number("abc2") is False
    assert is_valid_line_number("2 3") is False
    assert is_valid_line_number("2-3") is False
    assert is_valid_line_number("2+3") is False


def test_scientific_notation_strings():
    assert is_valid_line_number("2e1") is False
    assert is_valid_line_number("1e2") is False
    assert is_valid_line_number("2E1") is False


def test_custom_object_with_int_conversion():
    class CustomIntObject:
        def __int__(self):
            return 5
    
    assert is_valid_line_number(CustomIntObject()) is False


def test_custom_object_with_str_conversion_to_valid_number():
    class CustomStrObject:
        def __str__(self):
            return "42"
    
    assert is_valid_line_number(CustomStrObject()) is False


def test_custom_object_with_both_str_and_int_methods():
    class ComplexConversionObject:
        def __str__(self):
            return "not a number"

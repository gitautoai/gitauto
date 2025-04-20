import pytest
from utils.detect_new_line import detect_line_break


def test_detect_line_break_crlf():
    text = "Hello\r\nWorld"
    assert detect_line_break(text) == "\r\n"


def test_detect_line_break_cr():
    text = "Hello\rWorld"
    assert detect_line_break(text) == "\r"


def test_detect_line_break_lf():
    text = "Hello\nWorld"
    assert detect_line_break(text) == "\n"


def test_detect_line_break_empty():
    text = ""
    assert detect_line_break(text) == "\n"


def test_detect_line_break_mixed():
    text = "Hello\r\nWorld\rTest\n"
    assert detect_line_break(text) == "\r\n"


def test_detect_line_break_single_character():
    text = "\r"
    assert detect_line_break(text) == "\r"


def test_detect_line_break_special_characters():
    text = "Special characters: !@#$%^&*()\nMore text"
    assert detect_line_break(text) == "\n"


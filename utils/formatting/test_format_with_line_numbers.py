from utils.formatting.format_with_line_numbers import format_content_with_line_numbers


def test_basic_formatting():
    """Test basic line number formatting."""
    content = "line1\nline2\nline3"
    result = format_content_with_line_numbers(file_path="test.py", content=content)

    assert "```test.py" in result
    assert "1:line1" in result
    assert "2:line2" in result
    assert "3:line3" in result
    assert result.endswith("```")


def test_single_line():
    """Test formatting with single line."""
    content = "single line"
    result = format_content_with_line_numbers(file_path="file.txt", content=content)

    assert "```file.txt" in result
    assert "1:single line" in result


def test_empty_content():
    """Test formatting with empty content."""
    result = format_content_with_line_numbers(file_path="empty.py", content="")

    assert "```empty.py" in result
    assert "1:" in result


def test_line_number_width_padding():
    """Test that line numbers are padded correctly for many lines."""
    lines = [f"line{i}" for i in range(1, 101)]
    content = "\n".join(lines)
    result = format_content_with_line_numbers(file_path="large.py", content=content)

    assert "  1:line1" in result
    assert " 10:line10" in result
    assert "100:line100" in result


def test_content_with_special_characters():
    """Test formatting with special characters."""
    content = "def foo():\n    return 'héllo 🌍'"
    result = format_content_with_line_numbers(file_path="special.py", content=content)

    assert "1:def foo():" in result
    assert "2:    return 'héllo 🌍'" in result


def test_preserves_indentation():
    """Test that indentation is preserved."""
    content = "class Foo:\n    def bar(self):\n        pass"
    result = format_content_with_line_numbers(file_path="indent.py", content=content)

    assert "1:class Foo:" in result
    assert "2:    def bar(self):" in result
    assert "3:        pass" in result


def test_file_path_in_code_fence():
    """Test that file path appears in code fence."""
    result = format_content_with_line_numbers(
        file_path="src/utils/helper.py", content="code"
    )

    assert "```src/utils/helper.py" in result

from unittest.mock import patch, call

import pytest
from utils.prompts.get_mode_prompt import get_mode_prompt


@pytest.fixture
def mock_xml_content():
    """Fixture providing sample XML content for testing."""
    return "<mode_instruction>\n  <role>Test content</role>\n</mode_instruction>"


@pytest.fixture
def mock_read_xml_file():
    """Fixture to mock the read_xml_file function."""
    with patch("utils.prompts.get_mode_prompt.read_xml_file") as mock:
        yield mock


def test_get_mode_prompt_comment_mode(mock_read_xml_file, mock_xml_content):
    """Test that get_mode_prompt returns correct content for comment mode."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_mode_prompt("comment")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/update_comment.xml")
    assert result == mock_xml_content


def test_get_mode_prompt_commit_mode(mock_read_xml_file, mock_xml_content):
    """Test that get_mode_prompt returns correct content for commit mode."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_mode_prompt("commit")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/commit_changes.xml")
    assert result == mock_xml_content


def test_get_mode_prompt_explore_mode(mock_read_xml_file, mock_xml_content):
    """Test that get_mode_prompt returns correct content for explore mode."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_mode_prompt("explore")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/explore_repo.xml")
    assert result == mock_xml_content


def test_get_mode_prompt_get_mode(mock_read_xml_file, mock_xml_content):
    """Test that get_mode_prompt returns correct content for get mode."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_mode_prompt("get")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/explore_repo.xml")
    assert result == mock_xml_content


def test_get_mode_prompt_search_mode(mock_read_xml_file, mock_xml_content):
    """Test that get_mode_prompt returns correct content for search mode."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_mode_prompt("search")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/search_google.xml")
    assert result == mock_xml_content


def test_get_mode_prompt_get_and_explore_use_same_file(
    mock_read_xml_file, mock_xml_content
):
    """Test that both 'get' and 'explore' modes use the same XML file."""
    mock_read_xml_file.return_value = mock_xml_content

    get_result = get_mode_prompt("get")
    explore_result = get_mode_prompt("explore")

    # Both should call the same file
    expected_calls = [
        call("utils/prompts/modes/explore_repo.xml"),
        call("utils/prompts/modes/explore_repo.xml"),
    ]
    mock_read_xml_file.assert_has_calls(expected_calls)
    assert get_result == explore_result == mock_xml_content


def test_get_mode_prompt_invalid_mode(mock_read_xml_file):
    """Test that get_mode_prompt returns None for invalid mode."""
    # This should not be possible with the Literal type, but test the logic
    result = get_mode_prompt("invalid")  # type: ignore

    mock_read_xml_file.assert_not_called()
    assert result is None


def test_get_mode_prompt_empty_string_mode(mock_read_xml_file):
    """Test that get_mode_prompt returns None for empty string mode."""
    result = get_mode_prompt("")  # type: ignore

    mock_read_xml_file.assert_not_called()
    assert result is None


def test_get_mode_prompt_none_mode(mock_read_xml_file):
    """Test that get_mode_prompt returns None for None mode."""
    result = get_mode_prompt(None)  # type: ignore

    mock_read_xml_file.assert_not_called()
    assert result is None


def test_get_mode_prompt_file_path_construction():
    """Test that file paths are constructed correctly for all modes."""
    expected_paths = {
        "comment": "utils/prompts/modes/update_comment.xml",
        "commit": "utils/prompts/modes/commit_changes.xml",
        "explore": "utils/prompts/modes/explore_repo.xml",
        "get": "utils/prompts/modes/explore_repo.xml",
        "search": "utils/prompts/modes/search_google.xml",
    }

    with patch("utils.prompts.get_mode_prompt.read_xml_file") as mock_read_xml_file:
        mock_read_xml_file.return_value = "test content"

        for mode, expected_path in expected_paths.items():
            get_mode_prompt(mode)
            mock_read_xml_file.assert_called_with(expected_path)
            mock_read_xml_file.reset_mock()


def test_get_mode_prompt_read_xml_file_exception_propagation(mock_read_xml_file):
    """Test that exceptions from read_xml_file are propagated."""
    mock_read_xml_file.side_effect = FileNotFoundError("File not found")

    with pytest.raises(FileNotFoundError, match="File not found"):
        get_mode_prompt("comment")


def test_get_mode_prompt_read_xml_file_permission_error(mock_read_xml_file):
    """Test that PermissionError from read_xml_file is propagated."""
    mock_read_xml_file.side_effect = PermissionError("Permission denied")

    with pytest.raises(PermissionError, match="Permission denied"):
        get_mode_prompt("commit")


def test_get_mode_prompt_read_xml_file_returns_empty_string(mock_read_xml_file):
    """Test that get_mode_prompt handles empty string return from read_xml_file."""
    mock_read_xml_file.return_value = ""

    result = get_mode_prompt("explore")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/explore_repo.xml")
    assert result == ""


def test_get_mode_prompt_read_xml_file_returns_none(mock_read_xml_file):
    """Test that get_mode_prompt handles None return from read_xml_file."""
    mock_read_xml_file.return_value = None

    result = get_mode_prompt("search")

    mock_read_xml_file.assert_called_once_with("utils/prompts/modes/search_google.xml")
    assert result is None


def test_get_mode_prompt_base_path_consistency():
    """Test that all file paths use the same base path."""
    base_path = "utils/prompts/modes"

    with patch("utils.prompts.get_mode_prompt.read_xml_file") as mock_read_xml_file:
        mock_read_xml_file.return_value = "test"

        modes = ["comment", "commit", "explore", "get", "search"]
        for mode in modes:
            get_mode_prompt(mode)

        # Verify all calls use the correct base path
        for call in mock_read_xml_file.call_args_list:
            file_path = call[0][0]
            assert file_path.startswith(base_path)


@pytest.mark.parametrize(
    "mode,expected_file",
    [
        ("comment", "utils/prompts/modes/update_comment.xml"),
        ("commit", "utils/prompts/modes/commit_changes.xml"),
        ("explore", "utils/prompts/modes/explore_repo.xml"),
        ("get", "utils/prompts/modes/explore_repo.xml"),
        ("search", "utils/prompts/modes/search_google.xml"),
    ],
)
def test_get_mode_prompt_parametrized_modes(mock_read_xml_file, mode, expected_file):
    """Test all valid modes with parametrized testing."""
    mock_content = f"<content for {mode}>"
    mock_read_xml_file.return_value = mock_content

    result = get_mode_prompt(mode)

    mock_read_xml_file.assert_called_once_with(expected_file)
    assert result == mock_content


def test_get_mode_prompt_multiple_calls_same_mode(mock_read_xml_file, mock_xml_content):
    """Test that multiple calls with the same mode work correctly."""
    mock_read_xml_file.return_value = mock_xml_content

    result1 = get_mode_prompt("comment")
    result2 = get_mode_prompt("comment")
    result3 = get_mode_prompt("comment")

    # Should be called 3 times with the same file
    assert mock_read_xml_file.call_count == 3
    for call_args in mock_read_xml_file.call_args_list:
        assert call_args[0][0] == "utils/prompts/modes/update_comment.xml"

    assert result1 == result2 == result3 == mock_xml_content


def test_get_mode_prompt_different_modes_different_files(mock_read_xml_file):
    """Test that different modes call different files."""
    mock_read_xml_file.return_value = "content"

    get_mode_prompt("comment")
    get_mode_prompt("commit")
    get_mode_prompt("search")

    expected_calls = [
        call("utils/prompts/modes/update_comment.xml"),
        call("utils/prompts/modes/commit_changes.xml"),
        call("utils/prompts/modes/search_google.xml"),
    ]
    mock_read_xml_file.assert_has_calls(expected_calls)


def test_get_mode_prompt_case_sensitivity(mock_read_xml_file):
    """Test that mode parameter is case sensitive."""
    # These should not match and return None
    invalid_modes = ["COMMENT", "Comment", "COMMIT", "Commit", "EXPLORE", "Explore"]

    for invalid_mode in invalid_modes:
        result = get_mode_prompt(invalid_mode)  # type: ignore
        assert result is None

    mock_read_xml_file.assert_not_called()


def test_get_mode_prompt_whitespace_handling(mock_read_xml_file):
    """Test that modes with whitespace are not accepted."""
    invalid_modes = [" comment", "comment ", " comment ", "com ment"]

    for invalid_mode in invalid_modes:
        result = get_mode_prompt(invalid_mode)  # type: ignore
        assert result is None

    mock_read_xml_file.assert_not_called()


def test_get_mode_prompt_return_value_passthrough(mock_read_xml_file):
    """Test that the return value from read_xml_file is passed through unchanged."""
    test_values = [
        "simple string",
        "<xml>content</xml>",
        "multi\nline\ncontent",
        "content with special chars: !@#$%^&*()",
        "",
        "   whitespace content   ",
    ]

    for test_value in test_values:
        mock_read_xml_file.return_value = test_value
        result = get_mode_prompt("comment")
        assert result == test_value
        mock_read_xml_file.reset_mock()

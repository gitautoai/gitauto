from unittest.mock import patch
import pytest

from utils.prompts.get_trigger_prompt import get_trigger_prompt


@pytest.fixture
def mock_xml_content():
    """Fixture providing sample XML content for testing."""
    return "<trigger_instruction>\n  Test instruction content\n</trigger_instruction>"


@pytest.fixture
def mock_read_xml_file():
    """Fixture to mock the read_xml_file function."""
    with patch("utils.prompts.get_trigger_prompt.read_xml_file") as mock:
        yield mock


def test_get_trigger_prompt_issue_comment(mock_read_xml_file, mock_xml_content):
    """Test that issue_comment trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("issue_comment")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_issue_label(mock_read_xml_file, mock_xml_content):
    """Test that issue_label trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("issue_label")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_test_failure(mock_read_xml_file, mock_xml_content):
    """Test that test_failure trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("test_failure")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/check_run.xml")


def test_get_trigger_prompt_review_comment(mock_read_xml_file, mock_xml_content):
    """Test that review_comment trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("review_comment")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/review.xml")


def test_get_trigger_prompt_pr_checkbox(mock_read_xml_file, mock_xml_content):
    """Test that pr_checkbox trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("pr_checkbox")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/pr_checkbox.xml")


def test_get_trigger_prompt_pr_merge(mock_read_xml_file, mock_xml_content):
    """Test that pr_merge trigger returns correct XML content."""
    mock_read_xml_file.return_value = mock_xml_content

    result = get_trigger_prompt("pr_merge")

    assert result == mock_xml_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/pr_merge.xml")


def test_get_trigger_prompt_unknown_trigger(mock_read_xml_file):
    """Test that unknown trigger returns None."""
    # Cast to bypass type checking for testing invalid input
    unknown_trigger = "unknown_trigger"

    result = get_trigger_prompt(unknown_trigger)  # type: ignore

    assert result is None
    mock_read_xml_file.assert_not_called()


def test_get_trigger_prompt_file_read_exception(mock_read_xml_file):
    """Test that function handles file read exceptions gracefully."""
    mock_read_xml_file.side_effect = FileNotFoundError("File not found")

    with pytest.raises(FileNotFoundError):
        get_trigger_prompt("issue_comment")

    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_empty_xml_content(mock_read_xml_file):
    """Test that function handles empty XML content."""
    mock_read_xml_file.return_value = ""

    result = get_trigger_prompt("issue_comment")

    assert result == ""
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_whitespace_xml_content(mock_read_xml_file):
    """Test that function handles XML content with only whitespace."""
    whitespace_content = "   \n\t  \n   "
    mock_read_xml_file.return_value = whitespace_content

    result = get_trigger_prompt("issue_comment")

    assert result == whitespace_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


@pytest.mark.parametrize(
    "trigger,expected_file",
    [
        ("issue_comment", "utils/prompts/triggers/issue.xml"),
        ("issue_label", "utils/prompts/triggers/issue.xml"),
        ("test_failure", "utils/prompts/triggers/check_run.xml"),
        ("review_comment", "utils/prompts/triggers/review.xml"),
        ("pr_checkbox", "utils/prompts/triggers/pr_checkbox.xml"),
        ("pr_merge", "utils/prompts/triggers/pr_merge.xml"),
    ],
)
def test_get_trigger_prompt_file_mapping(mock_read_xml_file, trigger, expected_file):
    """Test that each trigger maps to the correct XML file."""
    get_trigger_prompt(trigger)
    mock_read_xml_file.assert_called_once_with(expected_file)


def test_get_trigger_prompt_none_return_from_read_xml_file(mock_read_xml_file):
    """Test that function handles None return from read_xml_file."""
    mock_read_xml_file.return_value = None

    result = get_trigger_prompt("issue_comment")

    assert result is None
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_large_xml_content(mock_read_xml_file):
    """Test that function handles large XML content."""
    large_content = "<trigger_instruction>\n" + "x" * 10000 + "\n</trigger_instruction>"
    mock_read_xml_file.return_value = large_content

    result = get_trigger_prompt("issue_comment")

    assert result == large_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")


def test_get_trigger_prompt_special_characters_xml_content(mock_read_xml_file):
    """Test that function handles XML content with special characters."""
    special_content = "<trigger_instruction>\n  Special chars: àáâãäåæçèéêë ñòóôõö ùúûüý\n</trigger_instruction>"
    mock_read_xml_file.return_value = special_content

    result = get_trigger_prompt("issue_comment")

    assert result == special_content
    mock_read_xml_file.assert_called_once_with("utils/prompts/triggers/issue.xml")

from unittest.mock import patch, mock_open
import pytest

from services.supabase.usage.insert_usage import Trigger
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

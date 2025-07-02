from unittest.mock import patch
import pytest
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
    FileChecklistItem,
)


@pytest.fixture
def sample_checklist():
    """Fixture providing a sample checklist for testing."""
    return [
        FileChecklistItem(
            path="src/main.py",
            checked=True,
            coverage_info=" (Line: 85%, Function: 90%)",
            status="modified",
        ),
        FileChecklistItem(
            path="src/utils.py",
            checked=False,
            coverage_info="",
            status="added",
        ),
        FileChecklistItem(
            path="src/config.py",
            checked=True,
            coverage_info=" (Line: 100%)",
            status="removed",
        ),
    ]


@pytest.fixture
def empty_checklist():
    """Fixture providing an empty checklist for testing."""
    return []


@pytest.fixture
def single_item_checklist():
    """Fixture providing a single item checklist for testing."""
    return [
        FileChecklistItem(
            path="test.py",
            checked=True,
            coverage_info=" (Line: 75%, Function: 80%, Branch: 70%)",
            status="modified",
        )
    ]


def test_create_test_selection_comment_with_sample_checklist(sample_checklist):
    """Test create_test_selection_comment with a typical checklist."""
    branch_name = "feature/test-branch"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(sample_checklist, branch_name)
        
        # Verify the comment structure
        assert "## 🧪 Manage Tests?" in result
        assert "Select files to manage tests for (create, update, or remove):" in result
        assert "- [x] modified `src/main.py` (Line: 85%, Function: 90%)" in result
        assert "- [ ] added `src/utils.py`" in result
        assert "- [x] removed `src/config.py` (Line: 100%)" in result
        assert "- [ ] Yes, manage tests" in result
        assert "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR." in result
        assert "Reset command message" in result
        assert "Settings links here" in result
        
        # Verify reset command was called with correct branch name
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_with_empty_checklist(empty_checklist):
    """Test create_test_selection_comment with an empty checklist."""
    branch_name = "main"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(empty_checklist, branch_name)
        
        # Verify basic structure is present even with empty checklist
        assert "## 🧪 Manage Tests?" in result
        assert "Select files to manage tests for (create, update, or remove):" in result
        assert "- [ ] Yes, manage tests" in result
        assert "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR." in result
        assert "Reset command message" in result
        assert "Settings links here" in result
        
        # Verify no file entries are present
        assert "- [x]" not in result.split("- [ ] Yes, manage tests")[0]
        assert "- [ ]" not in result.split("- [ ] Yes, manage tests")[0]
        
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_with_single_item(single_item_checklist):
    """Test create_test_selection_comment with a single item checklist."""
    branch_name = "develop"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(single_item_checklist, branch_name)
        
        # Verify the single item is correctly formatted
        assert "- [x] modified `test.py` (Line: 75%, Function: 80%, Branch: 70%)" in result
        assert "## 🧪 Manage Tests?" in result
        assert "- [ ] Yes, manage tests" in result
        
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_checkbox_formatting():
    """Test that checkboxes are formatted correctly based on checked status."""
    checklist = [
        FileChecklistItem(
            path="checked.py",
            checked=True,
            coverage_info="",
            status="added",
        ),
        FileChecklistItem(
            path="unchecked.py",
            checked=False,
            coverage_info="",
            status="modified",
        ),
    ]
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, "test-branch")
        
        # Verify checkbox formatting
        assert "- [x] added `checked.py`" in result
        assert "- [ ] modified `unchecked.py`" in result
        
        mock_reset.assert_called_once_with("test-branch")


def test_create_test_selection_comment_different_statuses():
    """Test create_test_selection_comment with different file statuses."""
    checklist = [
        FileChecklistItem(
            path="added_file.py",
            checked=True,
            coverage_info="",
            status="added",
        ),
        FileChecklistItem(
            path="modified_file.py",
            checked=True,
            coverage_info="",
            status="modified",
        ),
        FileChecklistItem(
            path="removed_file.py",
            checked=False,
            coverage_info="",
            status="removed",
        ),
    ]
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, "status-test")
        
        # Verify different statuses are included
        assert "- [x] added `added_file.py`" in result
        assert "- [x] modified `modified_file.py`" in result
        assert "- [ ] removed `removed_file.py`" in result
        
        mock_reset.assert_called_once_with("status-test")


def test_create_test_selection_comment_coverage_info_variations():
    """Test create_test_selection_comment with various coverage info formats."""
    checklist = [
        FileChecklistItem(
            path="no_coverage.py",
            checked=True,
            coverage_info="",
            status="added",
        ),
        FileChecklistItem(
            path="with_coverage.py",
            checked=True,
            coverage_info=" (Line: 95%)",
            status="modified",
        ),
        FileChecklistItem(
            path="full_coverage.py",
            checked=True,
            coverage_info=" (Line: 85%, Function: 90%, Branch: 75%)",
            status="modified",
        ),
    ]
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, "coverage-test")
        
        # Verify coverage info is correctly included
        assert "- [x] added `no_coverage.py`" in result
        assert "- [x] modified `with_coverage.py` (Line: 95%)" in result
        assert "- [x] modified `full_coverage.py` (Line: 85%, Function: 90%, Branch: 75%)" in result
        
        mock_reset.assert_called_once_with("coverage-test")
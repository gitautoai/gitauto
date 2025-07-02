"""Unit tests for create_test_selection_comment function.

Tests the creation of test selection comments with various checklist configurations.
"""

from unittest.mock import patch

from services.webhook.utils.create_test_selection_comment import (
    FileChecklistItem,
    create_test_selection_comment,
)


def test_create_test_selection_comment_empty_checklist():
    """Test comment creation with empty checklist."""
    checklist = []
    branch_name = "feature/test-branch"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        expected_lines = [
            "## 🧪 Manage Tests?",
            "",
            "Select files to manage tests for (create, update, or remove):",
            "",
            "",
            "---",
            "",
            "- [ ] Yes, manage tests",
            "",
            "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR.",
            "Reset command message",
            "",
            "Settings links here"
        ]
        expected = "\n".join(expected_lines)
        
        assert result == expected
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_single_checked_file():
    """Test comment creation with single checked file."""
    checklist = [
        FileChecklistItem(
            path="src/main.py",
            checked=True,
            coverage_info=" (Line: 85%, Function: 90%)",
            status="modified"
        )
    ]
    branch_name = "feature/single-file"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        expected_lines = [
            "## 🧪 Manage Tests?",
            "",
            "Select files to manage tests for (create, update, or remove):",
            "",
            "- [x] modified `src/main.py` (Line: 85%, Function: 90%)",
            "",
            "---",
            "",
            "- [ ] Yes, manage tests",
            "",
            "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR.",
            "Reset command message",
            "",
            "Settings links here"
        ]
        expected = "\n".join(expected_lines)
        
        assert result == expected
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_single_unchecked_file():
    """Test comment creation with single unchecked file."""
    checklist = [
        FileChecklistItem(
            path="src/utils.py",
            checked=False,
            coverage_info="",
            status="added"
        )
    ]
    branch_name = "feature/new-file"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        expected_lines = [
            "## 🧪 Manage Tests?",
            "",
            "Select files to manage tests for (create, update, or remove):",
            "",
            "- [ ] added `src/utils.py`",
            "",
            "---",
            "",
            "- [ ] Yes, manage tests",
            "",
            "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR.",
            "Reset command message",
            "",
            "Settings links here"
        ]
        expected = "\n".join(expected_lines)
        
        assert result == expected
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_multiple_files():
    """Test comment creation with multiple files of different statuses."""
    checklist = [
        FileChecklistItem(
            path="src/main.py",
            checked=True,
            coverage_info=" (Line: 85%, Function: 90%)",
            status="modified"
        ),
        FileChecklistItem(
            path="src/new_feature.py",
            checked=False,
            coverage_info="",
            status="added"
        ),
        FileChecklistItem(
            path="src/deprecated.py",
            checked=True,
            coverage_info=" (Line: 0%)",
            status="removed"
        )
    ]
    branch_name = "feature/multiple-changes"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        expected_lines = [
            "## 🧪 Manage Tests?",
            "",
            "Select files to manage tests for (create, update, or remove):",
            "",
            "- [x] modified `src/main.py` (Line: 85%, Function: 90%)",
            "- [ ] added `src/new_feature.py`",
            "- [x] removed `src/deprecated.py` (Line: 0%)",
            "",
            "---",
            "",
            "- [ ] Yes, manage tests",
            "",
            "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR.",
            "Reset command message",
            "",
            "Settings links here"
        ]
        expected = "\n".join(expected_lines)
        
        assert result == expected
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_complex_coverage_info():
    """Test comment creation with complex coverage information."""
    checklist = [
        FileChecklistItem(
            path="src/complex.py",
            checked=True,
            coverage_info=" (Line: 75%, Function: 80%, Branch: 65%)",
            status="modified"
        )
    ]
    branch_name = "feature/complex-coverage"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        expected_lines = [
            "## 🧪 Manage Tests?",
            "",
            "Select files to manage tests for (create, update, or remove):",
            "",
            "- [x] modified `src/complex.py` (Line: 75%, Function: 80%, Branch: 65%)",
            "",
            "---",
            "",
            "- [ ] Yes, manage tests",
            "",
            "Click the checkbox and GitAuto will add/update/remove tests for the selected files to this PR.",
            "Reset command message",
            "",
            "Settings links here"
        ]
        expected = "\n".join(expected_lines)
        
        assert result == expected
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_special_characters_in_path():
    """Test comment creation with special characters in file paths."""
    checklist = [
        FileChecklistItem(
            path="src/special-file_name.py",
            checked=True,
            coverage_info=" (Line: 100%)",
            status="modified"
        )
    ]
    branch_name = "feature/special-chars"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify that special characters in file paths are handled correctly
        assert "- [x] modified `src/special-file_name.py` (Line: 100%)" in result
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_all_status_types():
    """Test comment creation with all possible file status types."""
    checklist = [
        FileChecklistItem(
            path="src/added.py",
            checked=True,
            coverage_info="",
            status="added"
        ),
        FileChecklistItem(
            path="src/modified.py",
            checked=False,
            coverage_info=" (Line: 50%)",
            status="modified"
        ),
        FileChecklistItem(
            path="src/removed.py",
            checked=True,
            coverage_info="",
            status="removed"
        )
    ]
    branch_name = "feature/all-statuses"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify all status types are included
        assert "- [x] added `src/added.py`" in result
        assert "- [ ] modified `src/modified.py` (Line: 50%)" in result
        assert "- [x] removed `src/removed.py`" in result
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_long_branch_name():
    """Test comment creation with a very long branch name."""
    checklist = [
        FileChecklistItem(
            path="src/test.py",
            checked=True,
            coverage_info="",
            status="modified"
        )
    ]
    branch_name = "feature/very-long-branch-name-that-might-cause-issues-with-formatting-or-display"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify the function handles long branch names correctly
        assert "- [x] modified `src/test.py`" in result
        mock_reset.assert_called_once_with(branch_name)
        
        # Verify the result is a valid string
        assert isinstance(result, str)
        assert len(result) > 0
        # Verify the comment structure is maintained
        assert result.count("\n") >= 10  # Should have multiple lines

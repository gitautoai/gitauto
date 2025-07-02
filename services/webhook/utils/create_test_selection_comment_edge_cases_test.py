"""Edge case tests for create_test_selection_comment function.

Tests various edge cases and special scenarios.
"""

from unittest.mock import patch

from services.webhook.utils.create_test_selection_comment import (
    FileChecklistItem,
    create_test_selection_comment,
)


def test_create_test_selection_comment_unicode_characters():
    """Test comment creation with unicode characters in file paths."""
    checklist = [
        FileChecklistItem(
            path="src/测试文件.py",
            checked=True,
            coverage_info=" (Line: 95%)",
            status="modified"
        ),
        FileChecklistItem(
            path="src/файл.py",
            checked=False,
            coverage_info="",
            status="added"
        )
    ]
    branch_name = "feature/unicode-支持"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify unicode characters are handled correctly
        assert "- [x] modified `src/测试文件.py` (Line: 95%)" in result
        assert "- [ ] added `src/файл.py`" in result
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_very_long_file_paths():
    """Test comment creation with very long file paths."""
    checklist = [
        FileChecklistItem(
            path="src/very/deeply/nested/directory/structure/with/many/levels/and/a/very/long/filename_that_might_cause_formatting_issues.py",
            checked=True,
            coverage_info=" (Line: 75%, Function: 80%, Branch: 65%)",
            status="modified"
        )
    ]
    branch_name = "feature/long-paths"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify long paths are handled correctly
        assert "src/very/deeply/nested/directory/structure/with/many/levels/and/a/very/long/filename_that_might_cause_formatting_issues.py" in result
        assert "(Line: 75%, Function: 80%, Branch: 65%)" in result
        mock_reset.assert_called_once_with(branch_name)


def test_create_test_selection_comment_zero_coverage():
    """Test comment creation with zero coverage information."""
    checklist = [
        FileChecklistItem(
            path="src/uncovered.py",
            checked=True,
            coverage_info=" (Line: 0%, Function: 0%, Branch: 0%)",
            status="modified"
        )
    ]
    branch_name = "feature/zero-coverage"
    
    with patch("services.webhook.utils.create_test_selection_comment.TEST_SELECTION_COMMENT_IDENTIFIER", "## 🧪 Manage Tests?"), \
         patch("services.webhook.utils.create_test_selection_comment.PRODUCT_NAME", "GitAuto"), \
         patch("services.webhook.utils.create_test_selection_comment.create_reset_command_message") as mock_reset, \
         patch("services.webhook.utils.create_test_selection_comment.SETTINGS_LINKS", "Settings links here"):
        
        mock_reset.return_value = "Reset command message"
        
        result = create_test_selection_comment(checklist, branch_name)
        
        # Verify zero coverage is displayed correctly
        assert "- [x] modified `src/uncovered.py` (Line: 0%, Function: 0%, Branch: 0%)" in result
        mock_reset.assert_called_once_with(branch_name)
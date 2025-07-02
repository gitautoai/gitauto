"""Integration tests for create_test_selection_comment function.

Tests the function with real dependencies to ensure proper integration.
"""

from services.webhook.utils.create_test_selection_comment import (
    FileChecklistItem,
    create_test_selection_comment,
)


def test_create_test_selection_comment_integration_real_dependencies():
    """Integration test with real dependencies (no mocking)."""
    checklist = [
        FileChecklistItem(
            path="src/main.py",
            checked=True,
            coverage_info=" (Line: 85%, Function: 90%)",
            status="modified"
        ),
        FileChecklistItem(
            path="src/utils.py",
            checked=False,
            coverage_info="",
            status="added"
        )
    ]
    branch_name = "feature/integration-test"
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify the result is a string
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Verify basic structure
    lines = result.split("\n")
    assert len(lines) > 10  # Should have multiple lines
    
    # Verify the comment identifier is present
    assert "## 🧪 Manage Tests?" in result
    
    # Verify the file entries are present
    assert "- [x] modified `src/main.py` (Line: 85%, Function: 90%)" in result
    assert "- [ ] added `src/utils.py`" in result
    
    # Verify the manage tests checkbox is present
    assert "- [ ] Yes, manage tests" in result
    
    # Verify the product name is included
    assert "GitAuto" in result
    
    # Verify settings links are included
    assert "turn off triggers" in result
    assert "update coding rules" in result
    assert "exclude files" in result
    assert "info@gitauto.ai" in result
    
    # Verify reset command is included
    assert "git checkout" in result
    assert "git push --force-with-lease" in result
    assert branch_name in result


def test_create_test_selection_comment_integration_empty_checklist():
    """Integration test with empty checklist."""
    checklist = []
    branch_name = "feature/empty-test"
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify the result is still valid
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Verify basic structure is maintained even with empty checklist
    assert "## 🧪 Manage Tests?" in result
    assert "Select files to manage tests for" in result
    assert "- [ ] Yes, manage tests" in result
    assert "GitAuto" in result
    assert branch_name in result


def test_create_test_selection_comment_integration_markdown_formatting():
    """Integration test to verify proper markdown formatting."""
    checklist = [
        FileChecklistItem(
            path="src/test.py",
            checked=True,
            coverage_info=" (Line: 100%)",
            status="modified"
        )
    ]
    branch_name = "feature/markdown-test"
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify markdown elements are properly formatted
    assert result.startswith("## 🧪 Manage Tests?")
    assert "---" in result  # Horizontal rule
    assert "`src/test.py`" in result  # Code formatting for file path
    assert "```bash" in result  # Code block for reset command
    assert "[turn off triggers]" in result  # Link formatting
    assert "[info@gitauto.ai](mailto:info@gitauto.ai)" in result  # Email link
    
    # Verify checkbox formatting
    assert "- [x]" in result  # Checked checkbox
    assert "- [ ]" in result  # Unchecked checkbox
    
    # Verify proper line breaks and structure
    lines = result.split("\n")
    assert "" in lines  # Should have empty lines for spacing
    assert lines[0] == "## 🧪 Manage Tests?"  # First line should be the header

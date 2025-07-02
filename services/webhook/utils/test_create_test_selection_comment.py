from unittest.mock import patch
import pytest
from services.webhook.utils.create_test_selection_comment import (
    create_test_selection_comment,
    FileChecklistItem,
)


def test_create_test_selection_comment_basic():
    """Test basic functionality of create_test_selection_comment."""
    checklist = [
        FileChecklistItem(
            path="src/main.py",
            checked=True,
            coverage_info=" (Line: 85%)",
            status="modified",
        ),
        FileChecklistItem(
            path="src/utils.py",
            checked=False,
            coverage_info="",
            status="added",
        ),
    ]
    branch_name = "test-branch"
    
    result = create_test_selection_comment(checklist, branch_name)
    
    # Verify basic structure
    assert "## 🧪 Manage Tests?" in result
    assert "Select files to manage tests for (create, update, or remove):" in result
    assert "- [x] modified `src/main.py` (Line: 85%)" in result
    assert "- [ ] added `src/utils.py`" in result
    assert "- [ ] Yes, manage tests" in result
    assert "GitAuto" in result
    assert branch_name in result


def test_create_test_selection_comment_empty_checklist():
    """Test create_test_selection_comment with empty checklist."""
    result = create_test_selection_comment([], "main")
    
    # Verify basic structure is present even with empty checklist
    assert "## 🧪 Manage Tests?" in result
    assert "Select files to manage tests for (create, update, or remove):" in result
    assert "- [ ] Yes, manage tests" in result
    assert "GitAuto" in result
    assert "main" in result
    
    # Verify no file entries are present before "Yes, manage tests"
    parts = result.split("- [ ] Yes, manage tests")
    assert "- [x]" not in parts[0]
    assert "- [ ]" not in parts[0]
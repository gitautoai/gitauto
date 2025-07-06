from unittest.mock import patch, MagicMock
import pytest
from services.github.trees.get_file_tree_list import get_file_tree_list
from services.github.types.github_types import BaseArgs


@pytest.fixture
def mock_base_args():
    """Fixture providing mock BaseArgs for testing."""
    return {
        "owner": "test_owner",
        "repo": "test_repo", 
        "base_branch": "main",
        "token": "test_token"
    }


@pytest.fixture
def mock_get_file_tree():
    """Fixture to mock get_file_tree function."""
    with patch("services.github.trees.get_file_tree_list.get_file_tree") as mock:
        yield mock


def test_get_file_tree_list_empty_tree(mock_get_file_tree, mock_base_args):
    """Test behavior when tree is empty."""
    mock_get_file_tree.return_value = []
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == []
    assert message == "Found 0 files across 1 directory levels."
    mock_get_file_tree.assert_called_once_with("test_owner", "test_repo", "main", "test_token")


def test_get_file_tree_list_single_file_root_level(mock_get_file_tree, mock_base_args):
    """Test with single file at root level."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "README.md"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["README.md"]
    assert message == "Found 1 files across 1 directory levels."


def test_get_file_tree_list_multiple_files_same_depth(mock_get_file_tree, mock_base_args):
    """Test with multiple files at same depth level."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "config.py"},
        {"type": "blob", "path": "main.py"},
        {"type": "blob", "path": "README.md"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["config.py", "main.py", "README.md"]
    assert message == "Found 3 files across 1 directory levels."


def test_get_file_tree_list_files_different_depths(mock_get_file_tree, mock_base_args):
    """Test with files at different depth levels."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "README.md"},
        {"type": "blob", "path": "src/main.py"},
        {"type": "blob", "path": "src/utils/helper.py"},
        {"type": "blob", "path": "tests/test_main.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    # Files are sorted alphabetically
    expected = ["README.md", "src/main.py", "src/utils/helper.py", "tests/test_main.py"]
    assert result == expected
    assert message == "Found 4 files across 3 directory levels."


def test_get_file_tree_list_skip_non_blob_items(mock_get_file_tree, mock_base_args):
    """Test that non-blob items (directories, etc.) are skipped."""
    mock_get_file_tree.return_value = [
        {"type": "tree", "path": "src"},
        {"type": "blob", "path": "README.md"},
        {"type": "tree", "path": "tests"},
        {"type": "blob", "path": "main.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["README.md", "main.py"]
    assert message == "Found 2 files across 1 directory levels."


def test_get_file_tree_list_with_max_files_limit(mock_get_file_tree, mock_base_args):
    """Test behavior when max_files limit is applied."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "file1.py"},
        {"type": "blob", "path": "file2.py"},
        {"type": "blob", "path": "file3.py"},
        {"type": "blob", "path": "file4.py"},
        {"type": "blob", "path": "file5.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, 3)
    
    assert len(result) == 3
    assert result == ["file1.py", "file2.py", "file3.py"]
    assert message == "Found 5 files across 1 directory levels but limited to 3 files for now."


def test_get_file_tree_list_max_files_not_exceeded(mock_get_file_tree, mock_base_args):
    """Test behavior when max_files limit is not exceeded."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "file1.py"},
        {"type": "blob", "path": "file2.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, 5)
    
    assert result == ["file1.py", "file2.py"]
    assert message == "Found 2 files across 1 directory levels."


def test_get_file_tree_list_max_files_zero(mock_get_file_tree, mock_base_args):
    """Test behavior when max_files is 0."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "file1.py"},
        {"type": "blob", "path": "file2.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, 0)
    
    assert result == []
    assert message == "Found 2 files across 1 directory levels but limited to 0 files for now."


def test_get_file_tree_list_max_files_none(mock_get_file_tree, mock_base_args):
    """Test behavior when max_files is None (no limit)."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "file1.py"},
        {"type": "blob", "path": "file2.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["file1.py", "file2.py"]
    assert message == "Found 2 files across 1 directory levels."


def test_get_file_tree_list_complex_directory_structure(mock_get_file_tree, mock_base_args):
    """Test with complex directory structure and multiple depth levels."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "README.md"},
        {"type": "blob", "path": "config.py"},
        {"type": "blob", "path": "src/main.py"},
        {"type": "blob", "path": "src/config.py"},
        {"type": "blob", "path": "src/utils/helper.py"},
        {"type": "blob", "path": "src/utils/constants.py"},
        {"type": "blob", "path": "tests/test_main.py"},
        {"type": "blob", "path": "tests/utils/test_helper.py"},
        {"type": "blob", "path": "docs/api/endpoints.md"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    # Expected order: depth 0, then depth 1, then depth 2, all alphabetically sorted
    expected = [
        "README.md", "config.py",  # depth 0
        "docs/api/endpoints.md", "src/config.py", "src/main.py", "tests/test_main.py",  # depth 1
        "src/utils/constants.py", "src/utils/helper.py", "tests/utils/test_helper.py"  # depth 2
    ]
    assert result == expected
    assert message == "Found 9 files across 3 directory levels."


def test_get_file_tree_list_alphabetical_sorting_within_depth(mock_get_file_tree, mock_base_args):
    """Test that files are sorted alphabetically within each depth level."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "zebra.py"},
        {"type": "blob", "path": "alpha.py"},
        {"type": "blob", "path": "beta.py"},
        {"type": "blob", "path": "src/zebra.py"},
        {"type": "blob", "path": "src/alpha.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    expected = ["alpha.py", "beta.py", "zebra.py", "src/alpha.py", "src/zebra.py"]
    assert result == expected
    assert message == "Found 5 files across 2 directory levels."


def test_get_file_tree_list_deep_nested_structure(mock_get_file_tree, mock_base_args):
    """Test with deeply nested directory structure."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "a/b/c/d/e/deep.py"},
        {"type": "blob", "path": "shallow.py"},
        {"type": "blob", "path": "a/medium.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    expected = ["shallow.py", "a/medium.py", "a/b/c/d/e/deep.py"]
    assert result == expected
    assert message == "Found 3 files across 6 directory levels."


def test_get_file_tree_list_base_args_extraction(mock_get_file_tree):
    """Test that BaseArgs values are correctly extracted."""
    base_args = {
        "owner": "custom_owner",
        "repo": "custom_repo",
        "base_branch": "develop",
        "token": "custom_token"
    }
    mock_get_file_tree.return_value = []
    
    get_file_tree_list(base_args, None)
    
    mock_get_file_tree.assert_called_once_with("custom_owner", "custom_repo", "develop", "custom_token")


def test_get_file_tree_list_final_alphabetical_sort(mock_get_file_tree, mock_base_args):
    """Test that final result is sorted alphabetically."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "z.py"},
        {"type": "blob", "path": "a.py"},
        {"type": "blob", "path": "m.py"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["a.py", "m.py", "z.py"]
    assert message == "Found 3 files across 1 directory levels."


@patch("services.github.trees.get_file_tree_list.get_file_tree")
def test_get_file_tree_list_exception_handling(mock_get_file_tree, mock_base_args):
    """Test that exceptions are handled by the decorator."""
    mock_get_file_tree.side_effect = Exception("Test exception")
    
    # The handle_exceptions decorator should return default_return_value=[] on exception
    result = get_file_tree_list(mock_base_args, None)
    
    assert result == []


def test_get_file_tree_list_edge_case_single_character_paths(mock_get_file_tree, mock_base_args):
    """Test with single character file paths."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "z"},
        {"type": "blob", "path": "a"},
        {"type": "blob", "path": "m"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    assert result == ["a", "m", "z"]
    assert message == "Found 3 files across 1 directory levels."


def test_get_file_tree_list_mixed_file_extensions(mock_get_file_tree, mock_base_args):
    """Test with files having different extensions."""
    mock_get_file_tree.return_value = [
        {"type": "blob", "path": "script.py"},
        {"type": "blob", "path": "README.md"},
        {"type": "blob", "path": "config.json"},
        {"type": "blob", "path": "style.css"},
        {"type": "blob", "path": "index.html"}
    ]
    
    result, message = get_file_tree_list(mock_base_args, None)
    
    expected = ["README.md", "config.json", "index.html", "script.py", "style.css"]
    assert result == expected
    assert message == "Found 5 files across 1 directory levels."

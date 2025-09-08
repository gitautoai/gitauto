from unittest.mock import patch
import pytest
from services.github.trees.get_file_tree_list import get_file_tree_list


@pytest.fixture
def base_args(test_owner, test_repo, test_token):
    return {
        "owner": test_owner,
        "repo": test_repo,
        "base_branch": "main",
        "token": test_token,
    }


@pytest.fixture
def mock_tree_items():
    return [
        {"path": "README.md", "type": "blob"},
        {"path": "main.py", "type": "blob"},
        {"path": "config.py", "type": "blob"},
        {"path": ".github", "type": "tree"},
        {"path": ".github/workflows", "type": "tree"},
        {"path": ".github/workflows/ci.yml", "type": "blob"},
        {"path": ".github/workflows/deploy.yml", "type": "blob"},
        {"path": ".github/ISSUE_TEMPLATE", "type": "tree"},
        {"path": ".github/ISSUE_TEMPLATE/bug_report.md", "type": "blob"},
        {"path": ".github/dependabot.yml", "type": "blob"},
        {"path": "services", "type": "tree"},
        {"path": "services/github", "type": "tree"},
        {"path": "services/openai", "type": "tree"},
        {"path": "services/github/trees", "type": "tree"},
        {"path": "services/github/trees/get_file_tree.py", "type": "blob"},
        {"path": "services/github/trees/get_file_tree_list.py", "type": "blob"},
        {"path": "services/github/files", "type": "tree"},
        {"path": "services/github/files/get_remote_file_content.py", "type": "blob"},
        {"path": "utils", "type": "tree"},
        {"path": "utils/error", "type": "tree"},
        {"path": "utils/error/handle_exceptions.py", "type": "blob"},
    ]


def test_get_file_tree_list_root_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args)

        expected_result = [
            ".github/",
            "services/",
            "utils/",
            "README.md",
            "config.py",
            "main.py",
        ]

        assert result == expected_result


def test_get_file_tree_list_services_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="services")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_github_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path=".github")

        expected_result = ["ISSUE_TEMPLATE/", "workflows/", "dependabot.yml"]

        assert result == expected_result


def test_get_file_tree_list_workflows_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path=".github/workflows")

        expected_result = ["ci.yml", "deploy.yml"]

        assert result == expected_result


def test_get_file_tree_list_services_github_trees_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="services/github/trees")

        expected_result = ["get_file_tree.py", "get_file_tree_list.py"]

        assert result == expected_result


def test_get_file_tree_list_nonexistent_directory(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="nonexistent")

        assert result == []


def test_get_file_tree_list_empty_repository(base_args):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = []

        result = get_file_tree_list(base_args)

        assert result == []


def test_get_file_tree_list_dir_path_with_trailing_slash(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="services/")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_dir_path_with_leading_slash(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="/services")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_exception_handling(base_args):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.side_effect = Exception("Network error")

        result = get_file_tree_list(base_args)

        assert result == []  # Default return value from handle_exceptions decorator


def test_get_file_tree_list_single_file_directory(base_args):
    # Test directory with only one file
    mock_single_file_tree = [
        {"path": "single", "type": "tree"},
        {"path": "single/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_single_file_tree

        result = get_file_tree_list(base_args, dir_path="single")

        expected_result = ["file.py"]

        assert result == expected_result


def test_get_file_tree_list_mixed_files_and_dirs(base_args):
    # Test directory with mixed files and subdirectories
    mock_mixed_tree = [
        {"path": "mixed", "type": "tree"},
        {"path": "mixed/subdir", "type": "tree"},
        {"path": "mixed/file1.py", "type": "blob"},
        {"path": "mixed/file2.txt", "type": "blob"},
        {"path": "mixed/subdir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_mixed_tree

        result = get_file_tree_list(base_args, dir_path="mixed")

        expected_result = ["subdir/", "file1.py", "file2.txt"]

        assert result == expected_result


def test_get_file_tree_list_none_tree_items(base_args):
    # Test when get_file_tree returns None (falsy but not empty list)
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = None

        result = get_file_tree_list(base_args)

        assert result == []


def test_get_file_tree_list_root_only_files(base_args):
    # Test root directory with only files (no directories)
    mock_files_only = [
        {"path": "file1.py", "type": "blob"},
        {"path": "file2.txt", "type": "blob"},
        {"path": "file3.md", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_files_only

        result = get_file_tree_list(base_args)

        expected_result = ["file1.py", "file2.txt", "file3.md"]

        assert result == expected_result


def test_get_file_tree_list_root_only_directories(base_args):
    # Test root directory with only directories (no files)
    mock_dirs_only = [
        {"path": "dir1", "type": "tree"},
        {"path": "dir2", "type": "tree"},
        {"path": "dir3", "type": "tree"},
        {"path": "dir1/file.py", "type": "blob"},
        {"path": "dir2/file.py", "type": "blob"},
        {"path": "dir3/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_dirs_only

        result = get_file_tree_list(base_args)

        expected_result = ["dir1/", "dir2/", "dir3/"]

        assert result == expected_result


def test_get_file_tree_list_unknown_item_types(base_args):
    # Test with items that have unknown types (not "blob" or "tree")
    mock_unknown_types = [
        {"path": "file1.py", "type": "blob"},
        {"path": "dir1", "type": "tree"},
        {"path": "unknown1", "type": "unknown"},
        {"path": "symlink1", "type": "symlink"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_unknown_types

        result = get_file_tree_list(base_args)

        expected_result = ["dir1/", "file1.py"]

        assert result == expected_result


def test_get_file_tree_list_dir_path_both_slashes(base_args, mock_tree_items):
    # Test directory path with both leading and trailing slashes
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="/services/")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_verify_get_file_tree_call(base_args, mock_tree_items):
    # Test that get_file_tree is called with correct parameters
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        get_file_tree_list(base_args, dir_path="services")

        mock_get_tree.assert_called_once_with(
            owner=base_args["owner"],
            repo=base_args["repo"],
            ref=base_args["base_branch"],
            token=base_args["token"],
        )


def test_get_file_tree_list_directory_only_subdirectories(base_args):
    # Test directory that contains only subdirectories (no direct files)
    mock_subdirs_only = [
        {"path": "parent", "type": "tree"},
        {"path": "parent/subdir1", "type": "tree"},
        {"path": "parent/subdir2", "type": "tree"},
        {"path": "parent/subdir1/file.py", "type": "blob"},
        {"path": "parent/subdir2/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_subdirs_only

        result = get_file_tree_list(base_args, dir_path="parent")

        expected_result = ["subdir1/", "subdir2/"]

        assert result == expected_result


def test_get_file_tree_list_directory_only_files(base_args):
    # Test directory that contains only files (no subdirectories)
    mock_files_only = [
        {"path": "parent", "type": "tree"},
        {"path": "parent/file1.py", "type": "blob"},
        {"path": "parent/file2.txt", "type": "blob"},
        {"path": "parent/file3.md", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_files_only

        result = get_file_tree_list(base_args, dir_path="parent")

        expected_result = ["file1.py", "file2.txt", "file3.md"]

        assert result == expected_result


def test_get_file_tree_list_empty_dir_path_string(base_args, mock_tree_items):
    # Test with empty string dir_path (should behave like root directory)
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="")

        expected_result = [
            ".github/",
            "services/",
            "utils/",
            "README.md",
            "config.py",
            "main.py",
        ]

        assert result == expected_result


def test_get_file_tree_list_deep_nested_path(base_args):
    # Test with deeply nested directory path
    mock_deep_tree = [
        {"path": "a", "type": "tree"},
        {"path": "a/b", "type": "tree"},
        {"path": "a/b/c", "type": "tree"},
        {"path": "a/b/c/d", "type": "tree"},
        {"path": "a/b/c/file1.py", "type": "blob"},
        {"path": "a/b/c/file2.py", "type": "blob"},
        {"path": "a/b/c/d/deep_file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_deep_tree

        result = get_file_tree_list(base_args, dir_path="a/b/c")

        expected_result = ["d/", "file1.py", "file2.py"]

        assert result == expected_result


def test_get_file_tree_list_path_edge_cases(base_args):
    # Test edge cases for path matching
    mock_edge_cases = [
        {"path": "test", "type": "tree"},
        {"path": "test_similar", "type": "tree"},
        {"path": "test/file.py", "type": "blob"},
        {"path": "test_similar/file.py", "type": "blob"},
        {"path": "testing", "type": "tree"},
        {"path": "testing/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_edge_cases

        result = get_file_tree_list(base_args, dir_path="test")

        expected_result = ["file.py"]

        assert result == expected_result


def test_get_file_tree_list_nested_items_not_direct_children(base_args):
    # Test that nested items (not direct children) are not included
    mock_nested_tree = [
        {"path": "parent", "type": "tree"},
        {"path": "parent/child", "type": "tree"},
        {"path": "parent/file.py", "type": "blob"},
        {"path": "parent/child/nested_file.py", "type": "blob"},
        {"path": "parent/child/deep", "type": "tree"},
        {"path": "parent/child/deep/very_deep_file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_nested_tree

        result = get_file_tree_list(base_args, dir_path="parent")

        # Should only include direct children, not nested items
        expected_result = ["child/", "file.py"]

        assert result == expected_result


def test_get_file_tree_list_with_kwargs_parameter(base_args, mock_tree_items):
    # Test that the function accepts **_kwargs parameter without issues
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        # Pass additional kwargs that should be ignored
        result = get_file_tree_list(
            base_args, 
            dir_path="services", 
            extra_param="ignored",
            another_param=123
        )

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_directory_with_only_slash(base_args, mock_tree_items):
    # Test directory path that is just a slash
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="/")

        # Should behave like root directory after stripping slashes
        expected_result = [
            ".github/",
            "services/",
            "utils/",
            "README.md",
            "config.py",
            "main.py",
        ]

        assert result == expected_result


def test_get_file_tree_list_directory_with_multiple_slashes(base_args, mock_tree_items):
    # Test directory path with multiple slashes
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="//services//")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_empty_files_and_dirs_lists(base_args):
    # Test scenario where files and dirs lists are empty but tree_items is not
    mock_no_matches = [
        {"path": "other", "type": "tree"},
        {"path": "other/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_no_matches

        result = get_file_tree_list(base_args, dir_path="nonexistent")

        # Should return empty list when no matches found
        assert result == []


def test_get_file_tree_list_path_startswith_but_not_exact_match(base_args):
    # Test paths that start with dir_path but are not exact matches
    mock_similar_paths = [
        {"path": "test", "type": "tree"},
        {"path": "test123", "type": "tree"},
        {"path": "test/file.py", "type": "blob"},
        {"path": "test123/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_similar_paths

        result = get_file_tree_list(base_args, dir_path="test")

        # Should only include items from "test/" not "test123/"
        expected_result = ["file.py"]

        assert result == expected_result


def test_get_file_tree_list_whitespace_in_dir_path(base_args, mock_tree_items):
    # Test directory path with whitespace that gets stripped
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="  services  ")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_sorting_behavior(base_args):
    # Test that directories come before files and both are sorted alphabetically
    mock_unsorted = [
        {"path": "root", "type": "tree"},
        {"path": "root/zebra.py", "type": "blob"},
        {"path": "root/alpha", "type": "tree"},
        {"path": "root/beta.py", "type": "blob"},
        {"path": "root/gamma", "type": "tree"},
        {"path": "root/alpha/nested.py", "type": "blob"},
        {"path": "root/gamma/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_unsorted

        result = get_file_tree_list(base_args, dir_path="root")

        # Directories should come first, then files, both sorted alphabetically
        expected_result = ["alpha/", "gamma/", "beta.py", "zebra.py"]

        assert result == expected_result


def test_get_file_tree_list_root_with_complex_structure(base_args):
    # Test root directory with complex file/directory structure
    mock_complex_root = [
        {"path": "z_file.py", "type": "blob"},
        {"path": "a_dir", "type": "tree"},
        {"path": "m_file.txt", "type": "blob"},
        {"path": "b_dir", "type": "tree"},
        {"path": "a_dir/nested.py", "type": "blob"},
        {"path": "b_dir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_complex_root

        result = get_file_tree_list(base_args)

        # Should return sorted directories first, then sorted files
        expected_result = ["a_dir/", "b_dir/", "m_file.txt", "z_file.py"]

        assert result == expected_result
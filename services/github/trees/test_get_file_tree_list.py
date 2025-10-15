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

        assert result == []


def test_get_file_tree_list_single_file_directory(base_args):
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
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = None

        result = get_file_tree_list(base_args)

        assert result == []


def test_get_file_tree_list_root_only_files(base_args):
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
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(base_args, dir_path="/services/")

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_directory_only_subdirectories(base_args):
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

        expected_result = ["child/", "file.py"]

        assert result == expected_result


def test_get_file_tree_list_directory_with_only_tree_type_items(base_args):
    mock_only_trees = [
        {"path": "folder", "type": "tree"},
        {"path": "folder/subdir1", "type": "tree"},
        {"path": "folder/subdir2", "type": "tree"},
        {"path": "folder/subdir3", "type": "tree"},
        {"path": "folder/subdir1/nested.py", "type": "blob"},
        {"path": "folder/subdir2/nested.py", "type": "blob"},
        {"path": "folder/subdir3/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_only_trees

        result = get_file_tree_list(base_args, dir_path="folder")

        expected_result = ["subdir1/", "subdir2/", "subdir3/"]

        assert result == expected_result


def test_get_file_tree_list_directory_with_alternating_types(base_args):
    mock_alternating = [
        {"path": "alt", "type": "tree"},
        {"path": "alt/dir1", "type": "tree"},
        {"path": "alt/file1.py", "type": "blob"},
        {"path": "alt/dir2", "type": "tree"},
        {"path": "alt/file2.py", "type": "blob"},
        {"path": "alt/dir3", "type": "tree"},
        {"path": "alt/file3.py", "type": "blob"},
        {"path": "alt/dir1/nested.py", "type": "blob"},
        {"path": "alt/dir2/nested.py", "type": "blob"},
        {"path": "alt/dir3/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_alternating

        result = get_file_tree_list(base_args, dir_path="alt")

        expected_result = ["dir1/", "dir2/", "dir3/", "file1.py", "file2.py", "file3.py"]

        assert result == expected_result


def test_get_file_tree_list_root_with_mixed_types_and_unknown(base_args):
    mock_mixed_root = [
        {"path": "file.py", "type": "blob"},
        {"path": "dir", "type": "tree"},
        {"path": "unknown", "type": "unknown"},
        {"path": "dir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_mixed_root

        result = get_file_tree_list(base_args)

        expected_result = ["dir/", "file.py"]

        assert result == expected_result


def test_get_file_tree_list_directory_with_blob_then_tree(base_args):
    mock_blob_then_tree = [
        {"path": "mydir", "type": "tree"},
        {"path": "mydir/aaa_file.py", "type": "blob"},
        {"path": "mydir/bbb_file.py", "type": "blob"},
        {"path": "mydir/zzz_subdir", "type": "tree"},
        {"path": "mydir/zzz_subdir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_blob_then_tree

        result = get_file_tree_list(base_args, dir_path="mydir")

        expected_result = ["zzz_subdir/", "aaa_file.py", "bbb_file.py"]

        assert result == expected_result


def test_get_file_tree_list_kwargs_ignored(base_args, mock_tree_items):
    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_tree_items

        result = get_file_tree_list(
            base_args,
            dir_path="services",
            extra_param="ignored",
            another_param=123
        )

        expected_result = ["github/", "openai/"]

        assert result == expected_result


def test_get_file_tree_list_special_characters_in_path(base_args):
    mock_special_chars = [
        {"path": "my-folder", "type": "tree"},
        {"path": "my-folder/file_1.py", "type": "blob"},
        {"path": "my-folder/file-2.py", "type": "blob"},
        {"path": "my-folder/sub_dir", "type": "tree"},
        {"path": "my-folder/sub_dir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_special_chars

        result = get_file_tree_list(base_args, dir_path="my-folder")

        expected_result = ["sub_dir/", "file-2.py", "file_1.py"]

        assert result == expected_result


def test_get_file_tree_list_single_tree_item_in_directory(base_args):
    mock_single_tree = [
        {"path": "container", "type": "tree"},
        {"path": "container/only_subdir", "type": "tree"},
        {"path": "container/only_subdir/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_single_tree

        result = get_file_tree_list(base_args, dir_path="container")

        expected_result = ["only_subdir/"]

        assert result == expected_result


def test_get_file_tree_list_root_with_nested_structure(base_args):
    mock_nested_root = [
        {"path": "a", "type": "tree"},
        {"path": "b", "type": "tree"},
        {"path": "file.txt", "type": "blob"},
        {"path": "a/nested", "type": "tree"},
        {"path": "a/nested/deep.py", "type": "blob"},
        {"path": "b/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_nested_root

        result = get_file_tree_list(base_args)

        expected_result = ["a/", "b/", "file.txt"]

        assert result == expected_result


def test_get_file_tree_list_directory_path_not_matching_prefix(base_args):
    mock_no_match = [
        {"path": "folder1", "type": "tree"},
        {"path": "folder2", "type": "tree"},
        {"path": "folder1/file.py", "type": "blob"},
        {"path": "folder2/file.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_no_match

        result = get_file_tree_list(base_args, dir_path="folder3")

        assert result == []


def test_get_file_tree_list_multiple_slashes_in_dir_path(base_args):
    mock_multi_level = [
        {"path": "a", "type": "tree"},
        {"path": "a/b", "type": "tree"},
        {"path": "a/b/c", "type": "tree"},
        {"path": "a/b/file.py", "type": "blob"},
        {"path": "a/b/subdir", "type": "tree"},
        {"path": "a/b/c/deep.py", "type": "blob"},
        {"path": "a/b/subdir/nested.py", "type": "blob"},
    ]

    with patch(
        "services.github.trees.get_file_tree_list.get_file_tree"
    ) as mock_get_tree:
        mock_get_tree.return_value = mock_multi_level

        result = get_file_tree_list(base_args, dir_path="///a/b///")

        expected_result = ["c/", "subdir/", "file.py"]

        assert result == expected_result

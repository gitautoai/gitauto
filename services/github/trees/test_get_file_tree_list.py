from unittest.mock import patch
import pytest
from services.github.trees.get_file_tree_list import get_file_tree_list
from tests.constants import OWNER, REPO, TOKEN


@pytest.fixture
def base_args():
    return {
        "owner": OWNER,
        "repo": REPO,
        "base_branch": "main",
        "token": TOKEN,
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

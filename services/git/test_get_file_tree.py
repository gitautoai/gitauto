# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch, MagicMock

import pytest

from services.git.get_file_tree import get_file_tree


@pytest.fixture
def mock_run_subprocess():
    with patch("services.git.get_file_tree.run_subprocess") as mock:
        yield mock


GIT_LS_TREE_OUTPUT = """100644 blob abc123    1234\tsrc/main.py
100644 blob def456     567\tsrc/utils.py
040000 tree ghi789       -\tsrc/tests"""


class TestGetFileTree:
    @patch("os.path.isdir", return_value=True)
    def test_returns_tree_items(self, _mock_isdir, mock_run_subprocess):
        result = MagicMock()
        result.stdout = GIT_LS_TREE_OUTPUT
        mock_run_subprocess.return_value = result

        items = get_file_tree(clone_dir="/mnt/efs/owner/repo", ref="main")

        assert len(items) == 3
        assert items[0]["path"] == "src/main.py"
        assert items[0]["type"] == "blob"
        assert items[0].get("size") == 1234
        assert items[1]["path"] == "src/utils.py"
        assert items[2]["path"] == "src/tests"
        assert items[2]["type"] == "tree"
        assert "size" not in items[2]

    @patch("os.path.isdir", return_value=True)
    def test_uses_local_ref_directly(self, _mock_isdir, mock_run_subprocess):
        result = MagicMock()
        result.stdout = ""
        mock_run_subprocess.return_value = result

        get_file_tree(clone_dir="/mnt/efs/owner/repo", ref="main")

        # Should call git ls-tree with local ref, no fetch, no origin/ prefix
        call = mock_run_subprocess.call_args_list[0]
        assert call[1]["args"] == ["git", "ls-tree", "--full-tree", "-l", "-r", "main"]
        assert mock_run_subprocess.call_count == 1

    @patch("os.path.isdir", return_value=False)
    def test_returns_empty_for_invalid_clone_dir(
        self, _mock_isdir, mock_run_subprocess
    ):
        items = get_file_tree(clone_dir="/nonexistent", ref="main")

        assert not items
        assert isinstance(items, list)
        mock_run_subprocess.assert_not_called()

    @patch("os.path.isdir", return_value=True)
    def test_returns_empty_for_empty_output(self, _mock_isdir, mock_run_subprocess):
        result = MagicMock()
        result.stdout = ""
        mock_run_subprocess.return_value = result

        items = get_file_tree(clone_dir="/mnt/efs/owner/repo", ref="main")

        assert not items

    @patch("os.path.isdir", return_value=True)
    def test_root_only_flag(self, _mock_isdir, mock_run_subprocess):
        result = MagicMock()
        result.stdout = ""
        mock_run_subprocess.return_value = result

        get_file_tree(clone_dir="/mnt/efs/owner/repo", ref="main", root_only=True)

        call = mock_run_subprocess.call_args_list[0]
        assert "-r" not in call[1]["args"]

    @patch("os.path.isdir", return_value=True)
    def test_returns_empty_when_ls_tree_fails(self, _mock_isdir, mock_run_subprocess):
        mock_run_subprocess.side_effect = ValueError("ref not found")

        items = get_file_tree(clone_dir="/mnt/efs/owner/repo", ref="main")

        assert not items


# --- Integration tests (real git, local bare repo) ---


@pytest.mark.integration
def test_integration_get_file_tree_returns_all_files(local_repo):
    _, work_dir = local_repo
    items = get_file_tree(clone_dir=work_dir, ref="main")

    paths = {item["path"] for item in items}
    assert "README.md" in paths
    assert "src/main.py" in paths
    assert "src/utils.py" in paths

    blobs = [item for item in items if item["type"] == "blob"]
    assert len(blobs) >= 3
    for blob in blobs:
        assert blob.get("size", 0) > 0


@pytest.mark.integration
def test_integration_get_file_tree_root_only(local_repo):
    _, work_dir = local_repo
    items = get_file_tree(clone_dir=work_dir, ref="main", root_only=True)

    paths = {item["path"] for item in items}
    assert "README.md" in paths
    # root_only should list "src" as a tree, not recurse into it
    assert "src" in paths
    assert "src/main.py" not in paths

# pylint: disable=redefined-outer-name, unused-argument
from unittest.mock import MagicMock, patch

from services.efs.cleanup_stale_repos_on_efs import (
    _format_size,
    _get_dir_size,
    cleanup_stale_repos_on_efs,
    lambda_handler,
)

MODULE = "services.efs.cleanup_stale_repos_on_efs"


def test_cleanup_base_dir_does_not_exist():
    with patch(f"{MODULE}.os.path.exists", return_value=False):
        result = cleanup_stale_repos_on_efs("/mnt/efs")
    assert result == {"deleted": 0, "size_freed": 0}


def test_cleanup_empty_base_dir():
    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", return_value=[]),
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")
    assert result == {"deleted": 0, "size_freed": 0}
    mock_slack.assert_not_called()


def test_cleanup_skips_non_directory_at_owner_level():
    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", return_value=["file.txt"]),
        patch(f"{MODULE}.os.path.isdir", return_value=False),
        patch(f"{MODULE}.os.path.join", return_value="/mnt/efs/file.txt"),
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")
    assert result == {"deleted": 0, "size_freed": 0}
    mock_slack.assert_not_called()


def test_cleanup_skips_non_directory_at_repo_level():
    def mock_isdir(path):
        return path == "/mnt/efs/owner"

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["readme.md"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(
            f"{MODULE}.os.path.join",
            side_effect=["/mnt/efs/owner", "/mnt/efs/owner/readme.md"],
        ),
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")
    assert result == {"deleted": 0, "size_freed": 0}
    mock_slack.assert_not_called()


def test_cleanup_deletes_stale_repo():
    current_time = 1_000_000_000
    stale_mtime = current_time - (31 * 24 * 60 * 60)

    mock_stat = MagicMock()
    mock_stat.st_mtime = stale_mtime

    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(path):
        return path in ("/mnt/efs/owner", "/mnt/efs/owner/repo")

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["repo"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", return_value=mock_stat),
        patch(f"{MODULE}.time.time", return_value=current_time),
        patch(f"{MODULE}.shutil.rmtree") as mock_rmtree,
        patch(f"{MODULE}._get_dir_size", return_value=1024),
        patch(f"{MODULE}.slack_notify", return_value="ts123") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 1, "size_freed": 1024}
    mock_rmtree.assert_called_once_with("/mnt/efs/owner/repo")
    assert mock_slack.call_count == 3


def test_cleanup_keeps_fresh_repo():
    current_time = 1_000_000_000
    fresh_mtime = current_time - (5 * 24 * 60 * 60)

    mock_stat = MagicMock()
    mock_stat.st_mtime = fresh_mtime

    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(path):
        return path in ("/mnt/efs/owner", "/mnt/efs/owner/repo")

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["repo"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", return_value=mock_stat),
        patch(f"{MODULE}.time.time", return_value=current_time),
        patch(f"{MODULE}.shutil.rmtree") as mock_rmtree,
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 0, "size_freed": 0}
    mock_rmtree.assert_not_called()
    mock_slack.assert_not_called()


def test_cleanup_handles_os_error_on_stat():
    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(path):
        return path in ("/mnt/efs/owner", "/mnt/efs/owner/repo")

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["repo"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", side_effect=OSError("Permission denied")),
        patch(f"{MODULE}.time.time", return_value=1_000_000_000),
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 0, "size_freed": 0}
    mock_slack.assert_not_called()


def test_cleanup_slack_thread_ts_set_on_first_delete():
    current_time = 1_000_000_000
    stale_mtime = current_time - (31 * 24 * 60 * 60)

    mock_stat = MagicMock()
    mock_stat.st_mtime = stale_mtime

    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(_path):
        return True

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["repo1", "repo2"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", return_value=mock_stat),
        patch(f"{MODULE}.time.time", return_value=current_time),
        patch(f"{MODULE}.shutil.rmtree"),
        patch(f"{MODULE}._get_dir_size", return_value=2048),
        patch(f"{MODULE}.slack_notify", return_value="ts456") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 2, "size_freed": 4096}
    first_call_args = mock_slack.call_args_list[0]
    assert first_call_args[0][0] == "EFS cleanup: found stale repos"


def test_cleanup_slack_thread_ts_none_on_first_delete():
    current_time = 1_000_000_000
    stale_mtime = current_time - (31 * 24 * 60 * 60)

    mock_stat = MagicMock()
    mock_stat.st_mtime = stale_mtime

    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(_path):
        return True

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=[["owner"], ["repo"]]),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", return_value=mock_stat),
        patch(f"{MODULE}.time.time", return_value=current_time),
        patch(f"{MODULE}.shutil.rmtree"),
        patch(f"{MODULE}._get_dir_size", return_value=500),
        patch(f"{MODULE}.slack_notify", return_value=None) as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 1, "size_freed": 500}
    assert mock_slack.call_count == 2


def test_cleanup_no_summary_slack_when_no_deletions():
    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", return_value=[]),
        patch(f"{MODULE}.slack_notify") as mock_slack,
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 0, "size_freed": 0}
    mock_slack.assert_not_called()


def test_get_dir_size_with_files():
    mock_file = MagicMock()
    mock_file.is_file.return_value = True
    mock_file.is_dir.return_value = False
    mock_file.stat.return_value = MagicMock(st_size=100)

    mock_file2 = MagicMock()
    mock_file2.is_file.return_value = True
    mock_file2.is_dir.return_value = False
    mock_file2.stat.return_value = MagicMock(st_size=200)

    with patch(f"{MODULE}.os.scandir", return_value=[mock_file, mock_file2]):
        result = _get_dir_size("/some/path")

    assert result == 300


def test_get_dir_size_with_subdirectory():
    mock_subdir = MagicMock()
    mock_subdir.is_file.return_value = False
    mock_subdir.is_dir.return_value = True
    mock_subdir.path = "/some/path/subdir"

    mock_inner_file = MagicMock()
    mock_inner_file.is_file.return_value = True
    mock_inner_file.is_dir.return_value = False
    mock_inner_file.stat.return_value = MagicMock(st_size=50)

    with patch(f"{MODULE}.os.scandir", side_effect=[[mock_subdir], [mock_inner_file]]):
        result = _get_dir_size("/some/path")

    assert result == 50


def test_get_dir_size_permission_error():
    with patch(f"{MODULE}.os.scandir", side_effect=PermissionError("denied")):
        result = _get_dir_size("/some/path")

    assert result == 0


def test_get_dir_size_empty_directory():
    with patch(f"{MODULE}.os.scandir", return_value=[]):
        result = _get_dir_size("/some/path")

    assert result == 0


def test_format_size_bytes():
    assert _format_size(0) == "0.0 B"
    assert _format_size(512) == "512.0 B"
    assert _format_size(1023) == "1023.0 B"


def test_format_size_kilobytes():
    assert _format_size(1024) == "1.0 KB"
    assert _format_size(1536) == "1.5 KB"


def test_format_size_megabytes():
    assert _format_size(1024 * 1024) == "1.0 MB"
    assert _format_size(1.5 * 1024 * 1024) == "1.5 MB"


def test_format_size_gigabytes():
    assert _format_size(1024 * 1024 * 1024) == "1.0 GB"


def test_format_size_terabytes():
    assert _format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
    assert _format_size(2.5 * 1024 * 1024 * 1024 * 1024) == "2.5 TB"


def test_lambda_handler():
    with patch(
        f"{MODULE}.cleanup_stale_repos_on_efs",
        return_value={"deleted": 3, "size_freed": 9999},
    ) as mock_cleanup:
        result = lambda_handler({}, {})

    assert result == {"deleted": 3, "size_freed": 9999}
    mock_cleanup.assert_called_once()


def test_cleanup_multiple_owners_and_repos():
    current_time = 1_000_000_000
    stale_mtime = current_time - (31 * 24 * 60 * 60)
    fresh_mtime = current_time - (5 * 24 * 60 * 60)

    stale_stat = MagicMock()
    stale_stat.st_mtime = stale_mtime
    fresh_stat = MagicMock()
    fresh_stat.st_mtime = fresh_mtime

    def mock_join(*args):
        return "/".join(args)

    def mock_isdir(_path):
        return True

    def mock_listdir(path):
        if path == "/mnt/efs":
            return ["owner1", "owner2"]
        if path == "/mnt/efs/owner1":
            return ["stale-repo"]
        if path == "/mnt/efs/owner2":
            return ["fresh-repo"]
        return []

    def mock_stat(path):
        if "stale-repo" in path:
            return stale_stat
        return fresh_stat

    with (
        patch(f"{MODULE}.os.path.exists", return_value=True),
        patch(f"{MODULE}.os.listdir", side_effect=mock_listdir),
        patch(f"{MODULE}.os.path.isdir", side_effect=mock_isdir),
        patch(f"{MODULE}.os.path.join", side_effect=mock_join),
        patch(f"{MODULE}.os.stat", side_effect=mock_stat),
        patch(f"{MODULE}.time.time", return_value=current_time),
        patch(f"{MODULE}.shutil.rmtree") as mock_rmtree,
        patch(f"{MODULE}._get_dir_size", return_value=512),
        patch(f"{MODULE}.slack_notify", return_value="ts789"),
    ):
        result = cleanup_stale_repos_on_efs("/mnt/efs")

    assert result == {"deleted": 1, "size_freed": 512}
    mock_rmtree.assert_called_once_with("/mnt/efs/owner1/stale-repo")

# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.efs.cleanup_repo_efs import cleanup_repo_efs

MODULE = "services.efs.cleanup_repo_efs"


def test_deletes_efs_directory():
    with patch(f"{MODULE}.get_efs_dir") as mock_get_dir:
        with patch(f"{MODULE}.os.path.exists") as mock_exists:
            with patch(f"{MODULE}.shutil.rmtree") as mock_rmtree:
                with patch(f"{MODULE}.os.listdir") as mock_listdir:
                    with patch(f"{MODULE}.os.rmdir"):
                        mock_get_dir.return_value = "/mnt/efs/owner/repo"
                        mock_exists.side_effect = [True, True]
                        mock_listdir.return_value = []

                        result = cleanup_repo_efs("owner", "repo")

                        mock_rmtree.assert_called_once_with("/mnt/efs/owner/repo")
                        assert result is True


def test_returns_true_when_no_efs_directory():
    with patch(f"{MODULE}.get_efs_dir") as mock_get_dir:
        with patch(f"{MODULE}.os.path.exists") as mock_exists:
            mock_get_dir.return_value = "/mnt/efs/owner/repo"
            mock_exists.return_value = False

            result = cleanup_repo_efs("owner", "repo")

            assert result is True


def test_removes_empty_owner_directory():
    with patch(f"{MODULE}.get_efs_dir") as mock_get_dir:
        with patch(f"{MODULE}.os.path.exists") as mock_exists:
            with patch(f"{MODULE}.shutil.rmtree"):
                with patch(f"{MODULE}.os.listdir") as mock_listdir:
                    with patch(f"{MODULE}.os.rmdir") as mock_rmdir:
                        mock_get_dir.return_value = "/mnt/efs/owner/repo"
                        mock_exists.side_effect = [True, True]
                        mock_listdir.return_value = []

                        cleanup_repo_efs("owner", "repo")

                        mock_rmdir.assert_called_once_with("/mnt/efs/owner")

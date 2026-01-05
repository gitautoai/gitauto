from unittest.mock import patch

from services.efs.cleanup_repo_efs import cleanup_repo_efs


def test_cleanup_repo_efs_deletes_directory():
    with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
        with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
            with patch("services.efs.cleanup_repo_efs.shutil.rmtree") as mock_rmtree:
                with patch("services.efs.cleanup_repo_efs.os.listdir") as mock_listdir:
                    with patch("services.efs.cleanup_repo_efs.os.rmdir"):
                        mock_get_dir.return_value = "/mnt/efs/owner/repo"
                        mock_exists.side_effect = [True, True]
                        mock_listdir.return_value = []

                        result = cleanup_repo_efs("owner", "repo")

                        mock_rmtree.assert_called_once_with("/mnt/efs/owner/repo")
                        assert result is True


def test_cleanup_repo_efs_returns_false_when_no_directory():
    with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
        with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
            mock_get_dir.return_value = "/mnt/efs/owner/repo"
            mock_exists.return_value = False

            result = cleanup_repo_efs("owner", "repo")

            assert result is False


def test_cleanup_repo_efs_removes_empty_owner_directory():
    with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
        with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
            with patch("services.efs.cleanup_repo_efs.shutil.rmtree"):
                with patch("services.efs.cleanup_repo_efs.os.listdir") as mock_listdir:
                    with patch("services.efs.cleanup_repo_efs.os.rmdir") as mock_rmdir:
                        mock_get_dir.return_value = "/mnt/efs/owner/repo"
                        mock_exists.side_effect = [True, True]
                        mock_listdir.return_value = []

                        cleanup_repo_efs("owner", "repo")

                        mock_rmdir.assert_called_once_with("/mnt/efs/owner")


def test_cleanup_repo_efs_keeps_non_empty_owner_directory():
    with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
        with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
            with patch("services.efs.cleanup_repo_efs.shutil.rmtree"):
                with patch("services.efs.cleanup_repo_efs.os.listdir") as mock_listdir:
                    with patch("services.efs.cleanup_repo_efs.os.rmdir") as mock_rmdir:
                        mock_get_dir.return_value = "/mnt/efs/owner/repo"
                        mock_exists.side_effect = [True, True]
                        mock_listdir.return_value = ["other-repo"]

                        cleanup_repo_efs("owner", "repo")

                        mock_rmdir.assert_not_called()

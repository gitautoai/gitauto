# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.efs.cleanup_repo_efs import cleanup_repo_efs


def test_cleanup_repo_efs_deletes_s3_objects_and_efs_directory():
    with patch("services.efs.cleanup_repo_efs.s3_client") as mock_s3:
        with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
            with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
                with patch(
                    "services.efs.cleanup_repo_efs.shutil.rmtree"
                ) as mock_rmtree:
                    with patch(
                        "services.efs.cleanup_repo_efs.os.listdir"
                    ) as mock_listdir:
                        with patch("services.efs.cleanup_repo_efs.os.rmdir"):
                            mock_s3.list_objects_v2.return_value = {
                                "Contents": [
                                    {"Key": "owner/repo/node_modules.tar.gz"},
                                    {"Key": "owner/repo/manifests/package.json"},
                                ]
                            }
                            mock_get_dir.return_value = "/mnt/efs/owner/repo"
                            mock_exists.side_effect = [True, True]
                            mock_listdir.return_value = []

                            result = cleanup_repo_efs("owner", "repo")

                            assert mock_s3.delete_object.call_count == 2
                            mock_rmtree.assert_called_once_with("/mnt/efs/owner/repo")
                            assert result is True


def test_cleanup_repo_efs_handles_no_s3_objects():
    with patch("services.efs.cleanup_repo_efs.s3_client") as mock_s3:
        with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
            with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
                mock_s3.list_objects_v2.return_value = {"Contents": []}
                mock_get_dir.return_value = "/mnt/efs/owner/repo"
                mock_exists.return_value = False

                result = cleanup_repo_efs("owner", "repo")

                mock_s3.delete_object.assert_not_called()
                assert result is True


def test_cleanup_repo_efs_removes_empty_owner_directory():
    with patch("services.efs.cleanup_repo_efs.s3_client") as mock_s3:
        with patch("services.efs.cleanup_repo_efs.get_efs_dir") as mock_get_dir:
            with patch("services.efs.cleanup_repo_efs.os.path.exists") as mock_exists:
                with patch("services.efs.cleanup_repo_efs.shutil.rmtree"):
                    with patch(
                        "services.efs.cleanup_repo_efs.os.listdir"
                    ) as mock_listdir:
                        with patch(
                            "services.efs.cleanup_repo_efs.os.rmdir"
                        ) as mock_rmdir:
                            mock_s3.list_objects_v2.return_value = {}
                            mock_get_dir.return_value = "/mnt/efs/owner/repo"
                            mock_exists.side_effect = [True, True]
                            mock_listdir.return_value = []

                            cleanup_repo_efs("owner", "repo")

                            mock_rmdir.assert_called_once_with("/mnt/efs/owner")

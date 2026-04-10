import os
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from services.aws.s3.download_and_extract_dependency import download_and_extract_s3_deps


def test_skips_when_target_dirs_exist(tmp_path):
    clone_dir = str(tmp_path)
    os.makedirs(os.path.join(clone_dir, "mongodb-binaries"))
    os.makedirs(os.path.join(clone_dir, "node_modules"))
    os.makedirs(os.path.join(clone_dir, "vendor"))

    with patch("services.aws.s3.download_and_extract_dependency.s3_client") as mock_s3:
        download_and_extract_s3_deps("owner", "repo", clone_dir)
        mock_s3.download_file.assert_not_called()


def test_skips_when_s3_returns_no_such_key(tmp_path):
    clone_dir = str(tmp_path)

    with patch("services.aws.s3.download_and_extract_dependency.s3_client") as mock_s3:
        mock_s3.download_file.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        download_and_extract_s3_deps("owner", "repo", clone_dir)
        # Should not raise, just skip


def test_downloads_and_extracts_tarball(tmp_path):
    clone_dir = str(tmp_path)

    with patch(
        "services.aws.s3.download_and_extract_dependency.s3_client"
    ) as mock_s3, patch(
        "services.aws.s3.download_and_extract_dependency.subprocess.run"
    ) as mock_run, patch(
        "services.aws.s3.download_and_extract_dependency.os.remove"
    ):
        mock_s3.download_file.return_value = None
        mock_run.return_value = MagicMock(returncode=0)

        download_and_extract_s3_deps("owner", "repo", clone_dir)

        # Should have called download_file for mongodb-binaries, node_modules, and vendor
        assert mock_s3.download_file.call_count == 3
        assert mock_run.call_count == 3

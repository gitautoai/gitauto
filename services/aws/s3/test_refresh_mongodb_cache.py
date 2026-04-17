import os
from unittest.mock import patch

from services.aws.s3.refresh_mongodb_cache import refresh_mongodb_cache


def test_skips_when_no_mongodb_dir(tmp_path):
    refresh_mongodb_cache(
        owner_id=123,
        owner_name="owner",
        repo_name="repo",
        clone_dir=str(tmp_path),
    )
    # No error, just returns


def test_triggers_codebuild_when_mongodb_dir_exists(tmp_path):
    clone_dir = str(tmp_path)
    os.makedirs(os.path.join(clone_dir, "mongodb-binaries"))

    with patch(
        "services.aws.s3.refresh_mongodb_cache.detect_package_manager",
        return_value=("yarn", "yarn.lock", ""),
    ), patch(
        "services.aws.s3.refresh_mongodb_cache.detect_node_version",
        return_value="22",
    ), patch(
        "services.aws.s3.refresh_mongodb_cache.run_install_via_codebuild",
    ) as mock_codebuild:
        refresh_mongodb_cache(
            owner_id=123,
            owner_name="owner",
            repo_name="repo",
            clone_dir=clone_dir,
        )

        mock_codebuild.assert_called_once_with(
            s3_key_prefix="owner/repo",
            owner_id=123,
            pkg_manager="yarn",
            node_version="22",
        )

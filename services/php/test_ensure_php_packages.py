# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.php.ensure_php_packages import ensure_php_packages

MODULE = "services.php.ensure_php_packages"


def test_returns_false_when_no_composer_json():
    with patch(f"{MODULE}.read_local_file") as mock_get:
        mock_get.return_value = None

        result = ensure_php_packages(
            owner_id=123,
            clone_dir="/tmp/owner/repo",
            owner_name="owner",
            repo_name="repo",
        )

        assert result is False


def test_calls_shared_function_with_correct_args():
    def read_side_effect(filename, **_kwargs):
        if filename == "composer.json":
            return '{"require": {}}'
        if filename == "composer.lock":
            return '{"_readme": "lock"}'
        return None

    with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
        with patch(f"{MODULE}.get_dep_manifest_hash", return_value="abc123"):
            with patch(
                f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                return_value=True,
            ) as mock_check:
                result = ensure_php_packages(
                    owner_id=123,
                    clone_dir="/tmp/clone",
                    owner_name="owner",
                    repo_name="repo",
                )

                assert result is True
                mock_check.assert_called_once_with(
                    owner_name="owner",
                    repo_name="repo",
                    owner_id=123,
                    pkg_manager="composer",
                    tarball_name="vendor.tar.gz",
                    manifest_hash="abc123",
                    manifest_files={
                        "composer.json": '{"require": {}}',
                        "composer.lock": '{"_readme": "lock"}',
                    },
                    log_prefix="php",
                )


def test_excludes_lock_file_when_not_present():
    with patch(f"{MODULE}.read_local_file") as mock_get:
        mock_get.side_effect = ['{"require": {}}', None]
        with patch(f"{MODULE}.get_dep_manifest_hash", return_value="abc123"):
            with patch(
                f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                return_value=False,
            ) as mock_check:
                ensure_php_packages(
                    owner_id=123,
                    clone_dir="/tmp/clone",
                    owner_name="owner",
                    repo_name="repo",
                )

                manifest_files = mock_check.call_args.kwargs["manifest_files"]
                assert "composer.json" in manifest_files
                assert "composer.lock" not in manifest_files

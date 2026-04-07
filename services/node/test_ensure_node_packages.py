# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.node.ensure_node_packages import ensure_node_packages

MODULE = "services.node.ensure_node_packages"


def test_returns_false_when_no_package_json():
    with patch(f"{MODULE}.read_local_file") as mock_get:
        mock_get.return_value = None

        result = ensure_node_packages(
            owner_id=123,
            clone_dir="/tmp/owner/repo",
            owner_name="owner",
            repo_name="repo",
        )

        assert result is False


def test_calls_shared_function_with_correct_args():
    with patch(f"{MODULE}.read_local_file") as mock_get:
        # read_local_file calls: package.json, .npmrc, .nvmrc, .node-version
        mock_get.side_effect = ['{"name": "test"}', None, None, None]
        with patch(f"{MODULE}.detect_node_version", return_value="22"):
            with patch(
                f"{MODULE}.detect_package_manager",
                return_value=("npm", "package-lock.json", "lock-content"),
            ):
                with patch(f"{MODULE}.get_dep_manifest_hash", return_value="abc123"):
                    with patch(
                        f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                        return_value=True,
                    ) as mock_check:
                        result = ensure_node_packages(
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
                            pkg_manager="npm",
                            tarball_name="node_modules.tar.gz",
                            manifest_hash="abc123",
                            manifest_files={
                                "package.json": '{"name": "test"}',
                                "package-lock.json": "lock-content",
                            },
                            log_prefix="node",
                            node_version="22",
                        )


def test_sanitizes_http_to_https_in_npmrc():
    with patch(f"{MODULE}.read_local_file") as mock_get:
        # read_local_file calls: package.json, .npmrc, .nvmrc, .node-version
        mock_get.side_effect = [
            '{"name": "test"}',
            "registry=http://registry.npmjs.org/",
            None,
            None,
        ]
        with patch(f"{MODULE}.detect_node_version", return_value="22"):
            with patch(
                f"{MODULE}.detect_package_manager",
                return_value=("npm", None, None),
            ):
                with patch(f"{MODULE}.get_dep_manifest_hash", return_value="abc123"):
                    with patch(
                        f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                        return_value=False,
                    ) as mock_check:
                        ensure_node_packages(
                            owner_id=123,
                            clone_dir="/tmp/clone",
                            owner_name="owner",
                            repo_name="repo",
                        )

                        manifest_files = mock_check.call_args.kwargs["manifest_files"]
                        assert "https://registry.npmjs.org/" in manifest_files[".npmrc"]
                        assert (
                            "http://registry.npmjs.org/" not in manifest_files[".npmrc"]
                        )

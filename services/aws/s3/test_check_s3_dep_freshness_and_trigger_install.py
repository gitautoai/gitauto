# pyright: reportUnusedVariable=false
from unittest.mock import patch

from botocore.exceptions import ClientError

from services.aws.s3.check_s3_dep_freshness_and_trigger_install import (
    check_s3_dep_freshness_and_trigger_install,
)

MODULE = "services.aws.s3.check_s3_dep_freshness_and_trigger_install"


def test_returns_true_when_s3_tarball_is_fresh():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.head_object.return_value = {"Metadata": {"manifest-hash": "abc123"}}

        result = check_s3_dep_freshness_and_trigger_install(
            owner_name="owner",
            repo_name="repo",
            owner_id=123,
            pkg_manager="npm",
            tarball_name="node_modules.tar.gz",
            manifest_hash="abc123",
            manifest_files={"package.json": "{}"},
            log_prefix="node",
        )

        assert result is True
        mock_s3.put_object.assert_not_called()


def test_triggers_codebuild_when_hash_differs():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.head_object.return_value = {"Metadata": {"manifest-hash": "old_hash"}}
        with patch(f"{MODULE}.run_install_via_codebuild") as mock_codebuild:
            result = check_s3_dep_freshness_and_trigger_install(
                owner_name="owner",
                repo_name="repo",
                owner_id=123,
                pkg_manager="npm",
                tarball_name="node_modules.tar.gz",
                manifest_hash="new_hash",
                manifest_files={"package.json": "{}"},
                log_prefix="node",
            )

            assert result is False
            mock_codebuild.assert_called_once()


def test_triggers_codebuild_when_no_tarball():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        with patch(f"{MODULE}.run_install_via_codebuild") as mock_codebuild:
            result = check_s3_dep_freshness_and_trigger_install(
                owner_name="owner",
                repo_name="repo",
                owner_id=123,
                pkg_manager="npm",
                tarball_name="node_modules.tar.gz",
                manifest_hash="abc123",
                manifest_files={"package.json": "{}"},
                log_prefix="node",
            )

            assert result is False
            mock_codebuild.assert_called_once()


def test_uploads_all_manifest_files():
    with patch(f"{MODULE}.s3_client") as mock_s3:
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )
        with patch(f"{MODULE}.run_install_via_codebuild"):
            check_s3_dep_freshness_and_trigger_install(
                owner_name="owner",
                repo_name="repo",
                owner_id=123,
                pkg_manager="npm",
                tarball_name="node_modules.tar.gz",
                manifest_hash="abc123",
                manifest_files={
                    "package.json": '{"name": "test"}',
                    ".npmrc": "registry=https://registry.npmjs.org/",
                    "yarn.lock": "lockfile",
                },
                log_prefix="node",
            )

            put_calls = mock_s3.put_object.call_args_list
            keys = [c.kwargs["Key"] for c in put_calls]
            assert "owner/repo/manifests/package.json" in keys
            assert "owner/repo/manifests/.npmrc" in keys
            assert "owner/repo/manifests/yarn.lock" in keys
            assert "owner/repo/manifests/.manifest-hash" in keys

# pylint: disable=import-outside-toplevel
from unittest.mock import patch


def test_run_install_via_codebuild_skips_non_prod():
    with patch("services.aws.run_install_via_codebuild.IS_PRD", False):
        from services.aws.run_install_via_codebuild import run_install_via_codebuild

        result = run_install_via_codebuild(
            s3_key_prefix="owner/repo", owner_id=123, pkg_manager="yarn"
        )

        assert result is None


def test_run_install_via_codebuild_starts_build():
    mock_response = {"build": {"id": "gitauto-package-install:build-123"}}

    with patch("services.aws.run_install_via_codebuild.IS_PRD", True):
        with patch(
            "services.aws.run_install_via_codebuild.codebuild_client"
        ) as mock_client:
            with patch(
                "services.aws.run_install_via_codebuild.get_npm_token"
            ) as mock_token:
                mock_client.start_build.return_value = mock_response
                mock_token.return_value = None

                from services.aws.run_install_via_codebuild import (
                    run_install_via_codebuild,
                )

                result = run_install_via_codebuild(
                    s3_key_prefix="owner/repo", owner_id=123, pkg_manager="npm"
                )

                mock_client.start_build.assert_called_once()
                call_args = mock_client.start_build.call_args
                assert call_args.kwargs["projectName"] == "gitauto-package-install"
                env_vars = call_args.kwargs["environmentVariablesOverride"]
                assert {
                    "name": "S3_BUCKET",
                    "value": "dependency-cache",
                    "type": "PLAINTEXT",
                } in env_vars
                assert {
                    "name": "S3_KEY_PREFIX",
                    "value": "owner/repo",
                    "type": "PLAINTEXT",
                } in env_vars
                assert {
                    "name": "PKG_MANAGER",
                    "value": "npm",
                    "type": "PLAINTEXT",
                } in env_vars
                assert result == "gitauto-package-install:build-123"


def test_run_install_via_codebuild_includes_npm_token():
    mock_response = {"build": {"id": "gitauto-package-install:build-456"}}

    with patch("services.aws.run_install_via_codebuild.IS_PRD", True):
        with patch(
            "services.aws.run_install_via_codebuild.codebuild_client"
        ) as mock_client:
            with patch(
                "services.aws.run_install_via_codebuild.get_npm_token"
            ) as mock_token:
                mock_client.start_build.return_value = mock_response
                mock_token.return_value = "npm_secret_token"

                from services.aws.run_install_via_codebuild import (
                    run_install_via_codebuild,
                )

                result = run_install_via_codebuild(
                    s3_key_prefix="owner/repo", owner_id=123, pkg_manager="yarn"
                )

                call_args = mock_client.start_build.call_args
                env_vars = call_args.kwargs["environmentVariablesOverride"]
                assert {
                    "name": "NPM_TOKEN",
                    "value": "npm_secret_token",
                    "type": "PLAINTEXT",
                } in env_vars
                assert result == "gitauto-package-install:build-456"

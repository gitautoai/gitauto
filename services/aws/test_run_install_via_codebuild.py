# pylint: disable=import-outside-toplevel
from unittest.mock import patch

from services.node.detect_package_manager import PACKAGE_MANAGER_TO_LOCK_FILE


def test_run_install_via_codebuild_skips_non_prod():
    with patch("services.aws.run_install_via_codebuild.IS_PRD", False):
        from services.aws.run_install_via_codebuild import run_install_via_codebuild

        result = run_install_via_codebuild("/mnt/efs/owner/repo", 123, "yarn")

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
                with patch(
                    "services.aws.run_install_via_codebuild._MONGOD_SCRIPT_SRC",
                    "/nonexistent",
                ):
                    mock_client.start_build.return_value = mock_response
                    mock_token.return_value = None

                    from services.aws.run_install_via_codebuild import (
                        run_install_via_codebuild,
                    )

                    result = run_install_via_codebuild(
                        "/mnt/efs/owner/repo", 123, "npm"
                    )

                mock_client.start_build.assert_called_once()
                call_args = mock_client.start_build.call_args
                assert call_args.kwargs["projectName"] == "gitauto-package-install"
                env_vars = call_args.kwargs["environmentVariablesOverride"]
                assert {
                    "name": "EFS_DIR",
                    "value": "/mnt/efs/owner/repo",
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
                with patch(
                    "services.aws.run_install_via_codebuild._MONGOD_SCRIPT_SRC",
                    "/nonexistent",
                ):
                    mock_client.start_build.return_value = mock_response
                    mock_token.return_value = "npm_secret_token"

                    from services.aws.run_install_via_codebuild import (
                        run_install_via_codebuild,
                    )

                    result = run_install_via_codebuild(
                        "/mnt/efs/owner/repo", 123, "yarn"
                    )

                call_args = mock_client.start_build.call_args
                env_vars = call_args.kwargs["environmentVariablesOverride"]
                assert {
                    "name": "NPM_TOKEN",
                    "value": "npm_secret_token",
                    "type": "PLAINTEXT",
                } in env_vars
                assert result == "gitauto-package-install:build-456"


def test_run_install_via_codebuild_copies_mongod_script_for_node(tmp_path):
    """Node.js package managers should copy the mongod download script to EFS."""
    mock_response = {"build": {"id": "build-789"}}
    efs_script = str(tmp_path / ".scripts" / "download_mongod_binary.mjs")

    with patch("services.aws.run_install_via_codebuild.IS_PRD", True):
        with patch(
            "services.aws.run_install_via_codebuild.codebuild_client"
        ) as mock_client:
            with patch(
                "services.aws.run_install_via_codebuild.get_npm_token",
                return_value=None,
            ):
                with patch(
                    "services.aws.run_install_via_codebuild._MONGOD_SCRIPT_EFS",
                    efs_script,
                ):
                    mock_client.start_build.return_value = mock_response

                    from services.aws.run_install_via_codebuild import (
                        run_install_via_codebuild,
                    )

                    for pkg_manager in PACKAGE_MANAGER_TO_LOCK_FILE:
                        run_install_via_codebuild(
                            "/mnt/efs/owner/repo", 123, pkg_manager
                        )

                    import os

                    assert os.path.isfile(efs_script)


def test_run_install_via_codebuild_skips_mongod_script_for_composer(tmp_path):
    """Composer (PHP) projects should NOT copy the mongod download script."""
    mock_response = {"build": {"id": "build-789"}}
    efs_script = str(tmp_path / ".scripts" / "download_mongod_binary.mjs")

    with patch("services.aws.run_install_via_codebuild.IS_PRD", True):
        with patch(
            "services.aws.run_install_via_codebuild.codebuild_client"
        ) as mock_client:
            with patch(
                "services.aws.run_install_via_codebuild.get_npm_token",
                return_value=None,
            ):
                with patch(
                    "services.aws.run_install_via_codebuild._MONGOD_SCRIPT_EFS",
                    efs_script,
                ):
                    mock_client.start_build.return_value = mock_response

                    from services.aws.run_install_via_codebuild import (
                        run_install_via_codebuild,
                    )

                    run_install_via_codebuild("/mnt/efs/owner/repo", 123, "composer")

                    import os

                    assert not os.path.isfile(efs_script)

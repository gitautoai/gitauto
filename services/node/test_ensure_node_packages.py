# pylint: disable=redefined-outer-name
import os
from unittest.mock import patch

import pytest

from config import UTF8
from services.node.ensure_node_packages import ensure_node_packages


@pytest.fixture
def efs_dir(tmp_path):
    return str(tmp_path)


def _setup_node_modules(
    efs_dir, package_json='{"name": "test"}', npmrc=None, binaries=None
):
    """Set up a fake node_modules directory with .bin, package.json, and optional .npmrc."""
    nm = os.path.join(efs_dir, "node_modules")
    bin_dir = os.path.join(nm, ".bin")
    os.makedirs(bin_dir)
    for b in binaries or ["eslint"]:
        with open(os.path.join(bin_dir, b), "w", encoding=UTF8) as f:
            f.write("")
    with open(os.path.join(efs_dir, "package.json"), "w", encoding=UTF8) as f:
        f.write(package_json)
    if npmrc is not None:
        with open(os.path.join(efs_dir, ".npmrc"), "w", encoding=UTF8) as f:
            f.write(npmrc)


def test_returns_false_when_no_package_json():
    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        mock_get.return_value = None

        result = ensure_node_packages(
            owner_id=123,
            efs_dir="/mnt/efs/owner/repo",
        )

        assert result is False


def test_reuses_when_content_matches(efs_dir):
    _setup_node_modules(efs_dir)

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = ['{"name": "test"}', None]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                result = ensure_node_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                assert result is True


def test_triggers_codebuild_when_no_node_modules(efs_dir):
    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = ['{"name": "test"}', None]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ) as mock_codebuild:
                    result = ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    mock_codebuild.assert_called_once()
                    assert result is False


def test_triggers_codebuild_when_content_differs(efs_dir):
    _setup_node_modules(efs_dir, package_json='{"name": "old"}')

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = ['{"name": "new"}', None]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ) as mock_codebuild:
                    result = ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    mock_codebuild.assert_called_once()
                    assert result is False


def test_triggers_codebuild_when_bin_missing(efs_dir):
    # node_modules exists but no .bin
    os.makedirs(os.path.join(efs_dir, "node_modules"))
    with open(os.path.join(efs_dir, "package.json"), "w", encoding=UTF8) as f:
        f.write('{"name": "test"}')

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = ['{"name": "test"}', None]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ) as mock_codebuild:
                    result = ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    mock_codebuild.assert_called_once()
                    assert result is False


def test_triggers_codebuild_when_bin_empty(efs_dir):
    os.makedirs(os.path.join(efs_dir, "node_modules", ".bin"))
    with open(os.path.join(efs_dir, "package.json"), "w", encoding=UTF8) as f:
        f.write('{"name": "test"}')

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = ['{"name": "test"}', None]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ) as mock_codebuild:
                    result = ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    mock_codebuild.assert_called_once()
                    assert result is False


def test_reuses_when_npmrc_matches(efs_dir):
    _setup_node_modules(efs_dir, npmrc="//registry.npmjs.org/:_authToken=${NPM_TOKEN}")

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = [
                '{"name": "test"}',
                "//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
            ]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                result = ensure_node_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                assert result is True


def test_triggers_codebuild_when_npmrc_differs(efs_dir):
    _setup_node_modules(efs_dir, npmrc="//registry.npmjs.org/:_authToken=${NPM_TOKEN}")

    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = [
                '{"name": "test"}',
                "//different-registry.npmjs.org/:_authToken=${NPM_TOKEN}",
            ]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ) as mock_codebuild:
                    result = ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    mock_codebuild.assert_called_once()
                    assert result is False


def test_sanitizes_http_to_https_in_npmrc(efs_dir):
    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = [
                '{"name": "test"}',
                "registry=http://registry.npmjs.org/",
            ]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ):
                    ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    npmrc_path = os.path.join(efs_dir, ".npmrc")
                    assert os.path.exists(npmrc_path)
                    with open(npmrc_path, encoding=UTF8) as f:
                        assert f.read() == "registry=https://registry.npmjs.org/"


def test_preserves_https_in_npmrc(efs_dir):
    with patch("services.node.ensure_node_packages.read_local_file") as mock_get:
        with patch(
            "services.node.ensure_node_packages.detect_package_manager",
            return_value=("npm", None, None),
        ):
            mock_get.side_effect = [
                '{"name": "test"}',
                "registry=https://registry.npmjs.org/",
            ]
            with patch("services.node.ensure_node_packages.fcntl.flock"):
                with patch(
                    "services.node.ensure_node_packages.run_install_via_codebuild"
                ):
                    ensure_node_packages(
                        owner_id=123,
                        efs_dir=efs_dir,
                    )

                    npmrc_path = os.path.join(efs_dir, ".npmrc")
                    with open(npmrc_path, encoding=UTF8) as f:
                        assert f.read() == "registry=https://registry.npmjs.org/"

# pylint: disable=redefined-outer-name
import os
from unittest.mock import patch

import pytest

from config import UTF8
from services.php.ensure_php_packages import ensure_php_packages


@pytest.fixture
def efs_dir(tmp_path):
    return str(tmp_path)


def test_returns_false_when_no_composer_json():
    with patch("services.php.ensure_php_packages.read_local_file") as mock_get:
        mock_get.return_value = None

        result = ensure_php_packages(
            owner_id=123,
            efs_dir="/mnt/efs/owner/repo",
        )

        assert result is False


def test_reuses_when_vendor_and_content_match(efs_dir):
    # Set up EFS with matching vendor, autoload, composer.json
    vendor_path = os.path.join(efs_dir, "vendor")
    os.makedirs(os.path.join(vendor_path, "autoload.php").rsplit("/", 1)[0])
    with open(os.path.join(vendor_path, "autoload.php"), "w", encoding=UTF8) as f:
        f.write("<?php // autoload")
    with open(os.path.join(efs_dir, "composer.json"), "w", encoding=UTF8) as f:
        f.write('{"require": {}}')

    def read_side_effect(filename, **_kwargs):
        if filename == "composer.json":
            return '{"require": {}}'
        return None

    with patch(
        "services.php.ensure_php_packages.read_local_file",
        side_effect=read_side_effect,
    ):
        with patch("services.php.ensure_php_packages.fcntl.flock"):
            result = ensure_php_packages(
                owner_id=123,
                efs_dir=efs_dir,
            )

            assert result is True


def test_triggers_codebuild_when_no_vendor(efs_dir):
    with patch("services.php.ensure_php_packages.read_local_file") as mock_get:
        mock_get.return_value = '{"require": {}}'
        with patch("services.php.ensure_php_packages.fcntl.flock"):
            with patch(
                "services.php.ensure_php_packages.run_install_via_codebuild"
            ) as mock_codebuild:
                result = ensure_php_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                mock_codebuild.assert_called_once_with(efs_dir, 123, "composer")
                assert result is False


def test_triggers_codebuild_when_content_differs(efs_dir):
    # Set up EFS with old composer.json
    vendor_path = os.path.join(efs_dir, "vendor")
    os.makedirs(vendor_path)
    with open(os.path.join(vendor_path, "autoload.php"), "w", encoding=UTF8) as f:
        f.write("<?php // autoload")
    with open(os.path.join(efs_dir, "composer.json"), "w", encoding=UTF8) as f:
        f.write('{"require": {"old": "1.0"}}')

    with patch("services.php.ensure_php_packages.read_local_file") as mock_get:
        mock_get.return_value = '{"require": {"new": "2.0"}}'
        with patch("services.php.ensure_php_packages.fcntl.flock"):
            with patch(
                "services.php.ensure_php_packages.run_install_via_codebuild"
            ) as mock_codebuild:
                result = ensure_php_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                mock_codebuild.assert_called_once()
                assert result is False


def test_triggers_codebuild_when_autoload_missing(efs_dir):
    # vendor exists but autoload.php missing
    os.makedirs(os.path.join(efs_dir, "vendor"))

    with patch("services.php.ensure_php_packages.read_local_file") as mock_get:
        mock_get.return_value = '{"require": {}}'
        with patch("services.php.ensure_php_packages.fcntl.flock"):
            with patch(
                "services.php.ensure_php_packages.run_install_via_codebuild"
            ) as mock_codebuild:
                result = ensure_php_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                mock_codebuild.assert_called_once()
                assert result is False


def test_triggers_codebuild_when_lock_differs(efs_dir):
    # Set up EFS with matching composer.json but different lock
    vendor_path = os.path.join(efs_dir, "vendor")
    os.makedirs(vendor_path)
    with open(os.path.join(vendor_path, "autoload.php"), "w", encoding=UTF8) as f:
        f.write("<?php // autoload")
    with open(os.path.join(efs_dir, "composer.json"), "w", encoding=UTF8) as f:
        f.write('{"require": {}}')
    with open(os.path.join(efs_dir, "composer.lock"), "w", encoding=UTF8) as f:
        f.write('{"_readme": "old"}')

    def read_side_effect(filename, **_kwargs):
        if filename == "composer.json":
            return '{"require": {}}'
        if filename == "composer.lock":
            return '{"_readme": "new"}'
        return None

    with patch(
        "services.php.ensure_php_packages.read_local_file",
        side_effect=read_side_effect,
    ):
        with patch("services.php.ensure_php_packages.fcntl.flock"):
            with patch(
                "services.php.ensure_php_packages.run_install_via_codebuild"
            ) as mock_codebuild:
                result = ensure_php_packages(
                    owner_id=123,
                    efs_dir=efs_dir,
                )

                mock_codebuild.assert_called_once()
                assert result is False

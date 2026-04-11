# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

from constants.aws import LAMBDA_DISTRO
from services.mongoms.get_archive_name import get_mongoms_archive_name


@patch(
    "services.mongoms.get_archive_name.get_mongo_version", return_value="v7.0-latest"
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_returns_archive_name(_mock_major, _mock_version):
    """mongoms <8 with detected version returns ARCHIVE_NAME."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == f"mongodb-linux-x86_64-{LAMBDA_DISTRO}-v7.0-latest.tgz"
    )


@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=9)
def test_mongoms_9x_returns_none(_mock_major):
    """mongoms >=8 returns None (DISTRO or auto-detection handles it)."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=10
)
def test_mongoms_10x_returns_none(_mock_major):
    """mongoms >=8 returns None."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=None
)
def test_no_mongoms_in_package_json(_mock_major):
    """mongodb-memory-server not in package.json."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch("services.mongoms.get_archive_name.get_mongo_version", return_value=None)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_no_version_returns_none(_mock_major, _mock_version):
    """mongoms <8 but no MongoDB version detected returns None."""
    assert get_mongoms_archive_name("/tmp/clone") is None

# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.mongoms.get_archive_name import get_mongoms_archive_name


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_with_explicit_version(_mock_major, _mock_version):
    """mongoms 7.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=9)
def test_mongoms_9x_with_explicit_7x_version(_mock_major, _mock_version):
    """mongoms 9.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version",
    return_value="v7.0-latest",
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=10
)
def test_mongoms_10x_with_explicit_7x_version(_mock_major, _mock_version):
    """mongoms 10.x with explicit v7.0-latest uses amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-v7.0-latest.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=9)
def test_mongoms_9x_no_explicit_version_uses_default(_mock_major, _mock_version):
    """mongoms 9.x with no explicit version falls back to default 6.0.9 with amazon2 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2-6.0.9.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=10
)
def test_mongoms_10x_no_explicit_version_uses_default(_mock_major, _mock_version):
    """mongoms 10.x with no explicit version falls back to default 7.0.11 with amazon2023 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-7.0.11.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=7)
def test_mongoms_7x_no_explicit_version_uses_default(_mock_major, _mock_version):
    """mongoms 7.x with no explicit version falls back to default 6.0.9 with amazon2 distro."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2-6.0.9.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=12
)
def test_mongoms_future_version_falls_back_to_latest_known(_mock_major, _mock_version):
    """mongoms 12.x (unmapped) falls back to highest known default (11 -> 8.2.1)."""
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == "mongodb-linux-x86_64-amazon2023-8.2.1.tgz"
    )


@patch(
    "services.mongoms.get_archive_name.get_mongodb_server_version", return_value=None
)
@patch("services.mongoms.get_archive_name.get_dependency_major_version", return_value=5)
def test_mongoms_old_version_returns_none(_mock_major, _mock_version):
    """mongoms 5.x (too old, not mapped) returns None."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch(
    "services.mongoms.get_archive_name.get_dependency_major_version", return_value=None
)
def test_no_mongoms_in_package_json(_mock_major):
    """mongodb-memory-server not in package.json."""
    assert get_mongoms_archive_name("/tmp/clone") is None

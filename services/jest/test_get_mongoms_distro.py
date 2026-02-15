# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.jest.get_mongoms_distro import get_mongoms_distro


@patch(
    "services.jest.get_mongoms_distro.read_local_file",
    return_value='{"config": {"mongodbMemoryServer": {"version": "6.0.14"}}}',
)
def test_sets_distro_for_mongo6(_mock_read):
    """MongoDB 6.x has no amazon2023 binary, so distro should be ubuntu-22.04."""
    assert get_mongoms_distro("/tmp/clone") == "ubuntu-22.04"


@patch(
    "services.jest.get_mongoms_distro.read_local_file",
    return_value='{"config": {"mongodbMemoryServer": {"version": "7.0.5"}}}',
)
def test_no_distro_for_mongo7(_mock_read):
    """MongoDB 7.0+ has native amazon2023 binaries, so no override needed."""
    assert get_mongoms_distro("/tmp/clone") is None


@patch(
    "services.jest.get_mongoms_distro.read_local_file",
    return_value='{"name": "test-repo", "version": "1.0.0"}',
)
def test_no_distro_when_no_config(_mock_read):
    """No mongodbMemoryServer config in package.json, so no override needed."""
    assert get_mongoms_distro("/tmp/clone") is None


@patch("services.jest.get_mongoms_distro.read_local_file", return_value=None)
def test_no_distro_when_no_package_json(_mock_read):
    """No package.json found, so no override needed."""
    assert get_mongoms_distro("/tmp/clone") is None

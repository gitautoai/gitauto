# pyright: reportUnusedVariable=false
from unittest.mock import mock_open, patch

from utils.system.read_os_release_pretty_name import read_os_release_pretty_name


def test_amazon_linux_2023_double_quoted():
    fake = (
        'NAME="Amazon Linux"\n'
        'VERSION="2023"\n'
        'ID="amzn"\n'
        'PRETTY_NAME="Amazon Linux 2023"\n'
    )
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=True
    ), patch(
        "utils.system.read_os_release_pretty_name.open", mock_open(read_data=fake)
    ):
        assert read_os_release_pretty_name() == "Amazon Linux 2023"


def test_debian_single_quoted():
    fake = "PRETTY_NAME='Debian GNU/Linux 12 (bookworm)'\n"
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=True
    ), patch(
        "utils.system.read_os_release_pretty_name.open", mock_open(read_data=fake)
    ):
        assert read_os_release_pretty_name() == "Debian GNU/Linux 12 (bookworm)"


def test_alpine_unquoted():
    fake = "ID=alpine\nPRETTY_NAME=Alpine Linux v3.19\n"
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=True
    ), patch(
        "utils.system.read_os_release_pretty_name.open", mock_open(read_data=fake)
    ):
        assert read_os_release_pretty_name() == "Alpine Linux v3.19"


def test_file_missing_returns_none():
    # macOS dev machines have no /etc/os-release.
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=False
    ):
        assert read_os_release_pretty_name() is None


def test_file_present_but_no_pretty_name_returns_none():
    fake = 'NAME="Some OS"\nVERSION="1"\n'
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=True
    ), patch(
        "utils.system.read_os_release_pretty_name.open", mock_open(read_data=fake)
    ):
        assert read_os_release_pretty_name() is None


def test_pretty_name_present_but_empty_returns_none():
    fake = 'PRETTY_NAME=""\n'
    with patch(
        "utils.system.read_os_release_pretty_name.os.path.exists", return_value=True
    ), patch(
        "utils.system.read_os_release_pretty_name.open", mock_open(read_data=fake)
    ):
        assert read_os_release_pretty_name() is None

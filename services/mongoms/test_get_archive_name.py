# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import os
from unittest.mock import patch

from constants.aws import LAMBDA_DISTRO
from services.mongoms.get_archive_name import get_mongoms_archive_name

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(filename: str):
    with open(os.path.join(FIXTURES_DIR, filename), encoding="utf-8") as f:
        return f.read()


def _mock_read_local_file(repo_fixture: str, mongoms_version: str):
    """Return a side_effect function that returns mongoms package.json for the first call and repo package.json for the second."""
    mongoms_pkg = f'{{"version": "{mongoms_version}"}}'
    repo_pkg = _load_fixture(repo_fixture)
    calls = iter([mongoms_pkg, repo_pkg])
    return lambda *args, **kwargs: next(calls)


@patch("services.mongoms.get_archive_name.os.path.isfile", return_value=True)
@patch("services.mongoms.get_archive_name.read_local_file")
def test_foxcom_payment_backend_7x(_mock_read, _mock_isfile):
    """foxcom-payment-backend: mongoms 7.6.3 (<8), MONGOMS_VERSION=v7.0-latest in test script. Needs ARCHIVE_NAME."""
    _mock_read.side_effect = _mock_read_local_file(
        "foxcom-payment-backend-package.json", "7.6.3"
    )
    assert (
        get_mongoms_archive_name("/tmp/clone")
        == f"mongodb-linux-x86_64-{LAMBDA_DISTRO}-v7.0-latest.tgz"
    )


@patch("services.mongoms.get_archive_name.os.path.isfile", return_value=True)
@patch("services.mongoms.get_archive_name.read_local_file")
def test_foxden_auth_service_9x_skipped(_mock_read, _mock_isfile):
    """foxden-auth-service: mongoms 9.5.0 (>=8), DISTRO or auto-detection handles it. Returns None."""
    _mock_read.side_effect = _mock_read_local_file(
        "foxden-auth-service-package.json", "9.5.0"
    )
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch("services.mongoms.get_archive_name.os.path.isfile", return_value=True)
@patch("services.mongoms.get_archive_name.read_local_file")
def test_foxden_billing_10x_skipped(_mock_read, _mock_isfile):
    """foxden-billing: mongoms 10.0.0 (>=8), returns None."""
    _mock_read.side_effect = _mock_read_local_file(
        "foxden-billing-package.json", "10.0.0"
    )
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch("services.mongoms.get_archive_name.os.path.isfile", return_value=False)
def test_no_mongoms_installed(_mock_isfile):
    """node_modules/mongodb-memory-server-core doesn't exist."""
    assert get_mongoms_archive_name("/tmp/clone") is None


@patch("services.mongoms.get_archive_name.os.path.isfile", return_value=True)
@patch("services.mongoms.get_archive_name.read_local_file")
def test_foxcom_forms_no_mongoms_in_deps(_mock_read, _mock_isfile):
    """foxcom-forms: mongoms 7.4.0 installed but no MongoDB version in config or scripts (hypothetical — tests we can detect absence)."""
    mongoms_pkg = '{"version": "7.4.0"}'
    repo_pkg = _load_fixture("foxcom-forms-package.json")
    _mock_read.side_effect = iter([mongoms_pkg, repo_pkg])
    assert get_mongoms_archive_name("/tmp/clone") is None

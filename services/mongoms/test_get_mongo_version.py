# pyright: reportUnusedVariable=false
import os
from unittest.mock import patch

from services.mongoms.get_mongo_version import get_mongo_version

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(filename: str):
    with open(os.path.join(FIXTURES_DIR, filename), encoding="utf-8") as f:
        return f.read()


@patch("services.mongoms.get_mongo_version.read_local_file")
def test_foxcom_payment_backend_version_from_scripts(_mock_read):
    """foxcom-payment-backend: MONGOMS_VERSION=v7.0-latest in test script."""
    _mock_read.return_value = _load_fixture("foxcom-payment-backend-package.json")
    assert get_mongo_version("/tmp/clone") == "v7.0-latest"


@patch("services.mongoms.get_mongo_version.read_local_file")
def test_foxden_auth_service_version_from_scripts(_mock_read):
    """foxden-auth-service: MONGOMS_VERSION=v7.0-latest in test script."""
    _mock_read.return_value = _load_fixture("foxden-auth-service-package.json")
    assert get_mongo_version("/tmp/clone") == "v7.0-latest"


@patch("services.mongoms.get_mongo_version.read_local_file")
def test_foxden_billing_no_version(_mock_read):
    """foxden-billing: no MONGOMS_VERSION in config or scripts."""
    _mock_read.return_value = _load_fixture("foxden-billing-package.json")
    assert get_mongo_version("/tmp/clone") is None


@patch("services.mongoms.get_mongo_version.read_local_file")
def test_foxcom_forms_no_version(_mock_read):
    """foxcom-forms: no MONGOMS_VERSION in config or scripts."""
    _mock_read.return_value = _load_fixture("foxcom-forms-package.json")
    assert get_mongo_version("/tmp/clone") is None


@patch("services.mongoms.get_mongo_version.read_local_file")
def test_no_package_json(_mock_read):
    """No package.json found."""
    _mock_read.return_value = None
    assert get_mongo_version("/tmp/clone") is None

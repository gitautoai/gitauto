# pyright: reportUnusedVariable=false
import os
from unittest.mock import patch

from services.mongoms.get_mongodb_server_version import get_mongodb_server_version

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(filename: str):
    with open(os.path.join(FIXTURES_DIR, filename), encoding="utf-8") as f:
        return f.read()


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_foxcom_payment_backend_version_from_scripts(_mock_read):
    """foxcom-payment-backend: MONGOMS_VERSION=v7.0-latest in test script."""
    _mock_read.return_value = _load_fixture("foxcom-payment-backend-package.json")
    assert get_mongodb_server_version("/tmp/clone") == "v7.0-latest"


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_foxden_auth_service_version_from_scripts(_mock_read):
    """foxden-auth-service: MONGOMS_VERSION=v7.0-latest in test script."""
    _mock_read.return_value = _load_fixture("foxden-auth-service-package.json")
    assert get_mongodb_server_version("/tmp/clone") == "v7.0-latest"


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_foxden_billing_no_version(_mock_read):
    """foxden-billing: no MONGOMS_VERSION in config or scripts."""
    _mock_read.return_value = _load_fixture("foxden-billing-package.json")
    assert get_mongodb_server_version("/tmp/clone") is None


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_foxcom_forms_no_version(_mock_read):
    """foxcom-forms: no MONGOMS_VERSION in config or scripts."""
    _mock_read.return_value = _load_fixture("foxcom-forms-package.json")
    assert get_mongodb_server_version("/tmp/clone") is None


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_no_package_json(_mock_read):
    """No package.json found."""
    _mock_read.return_value = None
    assert get_mongodb_server_version("/tmp/clone") is None


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_foxden_version_controller_version_from_jest_mongodb_config(_mock_read):
    """foxden-version-controller: version lives in jest-mongodb-config.js.

    This is the real customer repo that caused Foxquilt PR #203 to fail:
    GA's detection defaulted to 6.0.9 (amazon2 distro) because it never
    looked at jest-mongodb-config.js, where `binary.version: 'v8.0-latest'`
    is actually declared.
    """
    package_json = _load_fixture("foxcom-forms-package.json")
    jest_config = _load_fixture("foxden-version-controller-jest-mongodb-config.js")

    def _read_side_effect(path, _):
        if path == "package.json":
            return package_json
        if path == "jest-mongodb-config.js":
            return jest_config
        return None

    _mock_read.side_effect = _read_side_effect
    assert get_mongodb_server_version("/tmp/clone") == "v8.0-latest"


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_jest_mongodb_config_cjs_is_checked(_mock_read):
    """`.cjs` variant is checked too (same precedence as the upstream library)."""
    package_json = _load_fixture("foxcom-forms-package.json")
    cjs_content = (
        "module.exports = {\n"
        "  mongodbMemoryServerOptions: {\n"
        '    binary: { version: "v7.0.14" },\n'
        "  },\n"
        "};\n"
    )

    def _read_side_effect(path, _):
        if path == "package.json":
            return package_json
        if path == "jest-mongodb-config.cjs":
            return cjs_content
        return None

    _mock_read.side_effect = _read_side_effect
    assert get_mongodb_server_version("/tmp/clone") == "v7.0.14"


@patch("services.mongoms.get_mongodb_server_version.read_local_file")
def test_jest_mongodb_config_without_binary_version(_mock_read):
    """jest-mongodb-config.js present but without a binary.version key → still None."""
    package_json = _load_fixture("foxcom-forms-package.json")
    jest_config_no_version = (
        "module.exports = {\n"
        "  mongodbMemoryServerOptions: {\n"
        "    instance: { dbName: 'jest' },\n"
        "  },\n"
        "};\n"
    )

    def _read_side_effect(path, _):
        if path == "package.json":
            return package_json
        if path == "jest-mongodb-config.js":
            return jest_config_no_version
        return None

    _mock_read.side_effect = _read_side_effect
    assert get_mongodb_server_version("/tmp/clone") is None

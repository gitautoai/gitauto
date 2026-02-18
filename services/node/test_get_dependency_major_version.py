import json
from unittest.mock import patch

from services.node.get_dependency_major_version import get_dependency_major_version


def test_returns_major_version_from_dev_dependencies():
    pkg = json.dumps({"devDependencies": {"eslint": "^9.0.0"}})
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=pkg
    ):
        assert get_dependency_major_version("/clone", "eslint") == 9


def test_returns_major_version_from_dependencies():
    pkg = json.dumps({"dependencies": {"eslint": "~8.18.0"}})
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=pkg
    ):
        assert get_dependency_major_version("/clone", "eslint") == 8


def test_prefers_dev_dependencies_over_dependencies():
    pkg = json.dumps(
        {
            "devDependencies": {"eslint": "^9.0.0"},
            "dependencies": {"eslint": "^8.0.0"},
        }
    )
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=pkg
    ):
        assert get_dependency_major_version("/clone", "eslint") == 9


def test_returns_none_when_no_package_json():
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=None
    ):
        assert get_dependency_major_version("/clone", "eslint") is None


def test_returns_none_when_package_not_found():
    pkg = json.dumps({"devDependencies": {"prettier": "^3.0.0"}})
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=pkg
    ):
        assert get_dependency_major_version("/clone", "eslint") is None


def test_returns_none_for_invalid_json():
    with patch(
        "services.node.get_dependency_major_version.read_local_file",
        return_value="not json",
    ):
        assert get_dependency_major_version("/clone", "eslint") is None


def test_strips_semver_prefixes():
    pkg = json.dumps({"devDependencies": {"eslint": ">=9.5.0"}})
    with patch(
        "services.node.get_dependency_major_version.read_local_file", return_value=pkg
    ):
        assert get_dependency_major_version("/clone", "eslint") == 9

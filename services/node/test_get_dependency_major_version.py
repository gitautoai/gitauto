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
        "services.node.get_dependency_major_version.read_local_file",
        side_effect=[pkg, None],
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


def test_finds_transitive_dep_in_node_modules():
    # mongodb-memory-server is not in package.json but installed via @shelf/jest-mongodb
    root_pkg = json.dumps({"devDependencies": {"@shelf/jest-mongodb": "^4.1.0"}})
    transitive_pkg = json.dumps({"name": "mongodb-memory-server", "version": "9.2.0"})
    with patch(
        "services.node.get_dependency_major_version.read_local_file",
        side_effect=[root_pkg, transitive_pkg],
    ):
        assert get_dependency_major_version("/clone", "mongodb-memory-server") == 9


def test_returns_none_when_transitive_dep_also_missing():
    root_pkg = json.dumps({"devDependencies": {"jest": "^29.0.0"}})
    with patch(
        "services.node.get_dependency_major_version.read_local_file",
        side_effect=[root_pkg, None],
    ):
        assert get_dependency_major_version("/clone", "mongodb-memory-server") is None

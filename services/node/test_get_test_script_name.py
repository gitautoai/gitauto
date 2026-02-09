import json
import os
import tempfile

from config import UTF8
from services.node.get_test_script_name import get_test_script_name


def test_get_test_script_name_returns_script_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": "jest"}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == "test"


def test_get_test_script_name_returns_none_when_no_package_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_when_no_scripts():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"name": "test"}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_when_no_test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"build": "tsc"}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_for_empty_test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": ""}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_for_invalid_package_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        # package.json is a list instead of dict
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(["invalid"], f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_for_invalid_scripts():
    with tempfile.TemporaryDirectory() as tmpdir:
        # scripts is a list instead of dict
        package_json = {"scripts": ["invalid"]}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_returns_none_for_non_string_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        # test script is a number instead of string
        package_json = {"scripts": {"test": 123}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result is None


def test_get_test_script_name_prefers_test_unit_over_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {
            "scripts": {
                "test": "jest",
                "test:unit": "NODE_OPTIONS='--experimental-vm-modules' npx jest --selectProjects unit",
            }
        }
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == "test:unit"


def test_get_test_script_name_falls_back_to_test_when_no_test_unit():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": "jest"}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == "test"


def test_get_test_script_name_ignores_empty_test_unit():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_json = {"scripts": {"test": "jest", "test:unit": ""}}
        with open(os.path.join(tmpdir, "package.json"), "w", encoding=UTF8) as f:
            json.dump(package_json, f)
        result = get_test_script_name(tmpdir)
        assert result == "test"

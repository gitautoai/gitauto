from unittest.mock import patch

from services.python.detect_python_package_manager import (
    detect_python_package_manager,
)

MODULE = "services.python.detect_python_package_manager"


def test_detects_poetry_from_lock_file():
    def read_side_effect(filename, **_kwargs):
        if filename == "poetry.lock":
            return "[[package]]\nname = flask"
        return None

    with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
        pm, lock_file, content = detect_python_package_manager("/tmp/clone")
        assert pm == "poetry"
        assert lock_file == "poetry.lock"
        assert content == "[[package]]\nname = flask"


def test_detects_pipenv_from_lock_file():
    def read_side_effect(filename, **_kwargs):
        if filename == "poetry.lock":
            return None
        if filename == "Pipfile.lock":
            return '{"_meta": {"hash": {"sha256": "abc"}}}'
        return None

    with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
        pm, lock_file, content = detect_python_package_manager("/tmp/clone")
        assert pm == "pipenv"
        assert lock_file == "Pipfile.lock"
        assert content is not None
        assert "abc" in content


def test_defaults_to_pip_when_no_lock_file():
    with patch(f"{MODULE}.read_local_file", return_value=None):
        pm, lock_file, content = detect_python_package_manager("/tmp/clone")
        assert pm == "pip"
        assert lock_file is None
        assert content is None


def test_poetry_takes_priority_over_pipenv():
    def read_side_effect(filename, **_kwargs):
        if filename == "poetry.lock":
            return "poetry content"
        if filename == "Pipfile.lock":
            return "pipenv content"
        return None

    with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
        pm, lock_file, _ = detect_python_package_manager("/tmp/clone")
        assert pm == "poetry"
        assert lock_file == "poetry.lock"

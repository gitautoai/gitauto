from unittest.mock import patch

from services.node.detect_package_manager import detect_package_manager


def test_detect_yarn():
    def read_side_effect(file_path, **_kwargs):
        if file_path == "yarn.lock":
            return "yarn lock content"
        return None

    with patch(
        "services.node.detect_package_manager.read_local_file",
        side_effect=read_side_effect,
    ):
        pm, lock_file, content = detect_package_manager(local_dir="/tmp/repo")

        assert pm == "yarn"
        assert lock_file == "yarn.lock"
        assert content == "yarn lock content"


def test_detect_pnpm():
    def read_side_effect(file_path, **_kwargs):
        if file_path == "pnpm-lock.yaml":
            return "pnpm lock content"
        return None

    with patch(
        "services.node.detect_package_manager.read_local_file",
        side_effect=read_side_effect,
    ):
        pm, lock_file, content = detect_package_manager(local_dir="/tmp/repo")

        assert pm == "pnpm"
        assert lock_file == "pnpm-lock.yaml"
        assert content == "pnpm lock content"


def test_detect_bun():
    def read_side_effect(file_path, **_kwargs):
        if file_path == "bun.lockb":
            return "bun lock content"
        return None

    with patch(
        "services.node.detect_package_manager.read_local_file",
        side_effect=read_side_effect,
    ):
        pm, lock_file, content = detect_package_manager(local_dir="/tmp/repo")

        assert pm == "bun"
        assert lock_file == "bun.lockb"
        assert content == "bun lock content"


def test_detect_npm():
    def read_side_effect(file_path, **_kwargs):
        if file_path == "package-lock.json":
            return "npm lock content"
        return None

    with patch(
        "services.node.detect_package_manager.read_local_file",
        side_effect=read_side_effect,
    ):
        pm, lock_file, content = detect_package_manager(local_dir="/tmp/repo")

        assert pm == "npm"
        assert lock_file == "package-lock.json"
        assert content == "npm lock content"


def test_default_to_npm_when_no_lock_file():
    with patch(
        "services.node.detect_package_manager.read_local_file",
        return_value=None,
    ):
        pm, lock_file, content = detect_package_manager(local_dir="/tmp/repo")

        assert pm == "npm"
        assert lock_file is None
        assert content is None

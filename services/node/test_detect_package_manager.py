from unittest.mock import mock_open, patch

from services.node.detect_package_manager import detect_package_manager


def test_detect_yarn_from_clone_dir():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: "yarn.lock" in p
        with patch("builtins.open", mock_open(read_data="yarn lock content")):
            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "yarn"
            assert lock_file == "yarn.lock"
            assert content == "yarn lock content"


def test_detect_pnpm_from_clone_dir():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: "pnpm-lock.yaml" in p
        with patch("builtins.open", mock_open(read_data="pnpm lock content")):
            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "pnpm"
            assert lock_file == "pnpm-lock.yaml"
            assert content == "pnpm lock content"


def test_detect_bun_from_clone_dir():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: "bun.lockb" in p
        with patch("builtins.open", mock_open(read_data="bun lock content")):
            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "bun"
            assert lock_file == "bun.lockb"
            assert content == "bun lock content"


def test_detect_npm_from_clone_dir():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: "package-lock.json" in p
        with patch("builtins.open", mock_open(read_data="npm lock content")):
            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "npm"
            assert lock_file == "package-lock.json"
            assert content == "npm lock content"


def test_detect_yarn_from_github_api():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        with patch("services.node.detect_package_manager.get_raw_content") as mock_get:
            mock_exists.return_value = False
            mock_get.side_effect = lambda **kwargs: (
                "yarn api content" if kwargs["file_path"] == "yarn.lock" else None
            )

            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "yarn"
            assert lock_file == "yarn.lock"
            assert content == "yarn api content"


def test_default_to_npm_when_no_lock_file():
    with patch("services.node.detect_package_manager.os.path.exists") as mock_exists:
        with patch("services.node.detect_package_manager.get_raw_content") as mock_get:
            mock_exists.return_value = False
            mock_get.return_value = None

            pm, lock_file, content = detect_package_manager(
                local_dir="/tmp/repo",
                owner="owner",
                repo="repo",
                branch="main",
                token="token",
            )

            assert pm == "npm"
            assert lock_file is None
            assert content is None

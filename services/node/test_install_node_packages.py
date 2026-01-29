from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from services.node.install_node_packages import (
    _can_reuse_packages,
    install_node_packages,
)


def test_can_reuse_packages_returns_false_when_no_node_modules():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.return_value = False

        result = _can_reuse_packages("/mnt/efs/owner/repo", "{}")

        assert result is False


def test_can_reuse_packages_returns_true_when_content_matches():
    def exists_side_effect(path):
        if "node_modules" in path or "package.json" in path or ".bin" in path:
            return True
        if ".npmrc" in path:
            return False
        return False

    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.side_effect = exists_side_effect
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            with patch("builtins.open", mock_open(read_data='{"name": "test"}')):
                result = _can_reuse_packages(
                    "/mnt/efs/owner/repo",
                    '{"name": "test"}',
                )

                assert result is True


def test_can_reuse_packages_returns_false_when_content_differs():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            with patch("builtins.open", mock_open(read_data='{"name": "old"}')):
                result = _can_reuse_packages(
                    "/mnt/efs/owner/repo",
                    '{"name": "new"}',
                )

                assert result is False


def test_can_reuse_packages_returns_true_when_npmrc_matches():
    file_contents = {
        "package.json": '{"name": "test"}',
        ".npmrc": "//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
    }

    def open_side_effect(path, *_args, **_kwargs):
        for filename, content in file_contents.items():
            if filename in path:
                return mock_open(read_data=content)()
        return mock_open(read_data="")()

    with patch("services.node.install_node_packages.os.path.exists", return_value=True):
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            with patch("builtins.open", side_effect=open_side_effect):
                result = _can_reuse_packages(
                    "/mnt/efs/owner/repo",
                    '{"name": "test"}',
                    "//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
                )

                assert result is True


def test_can_reuse_packages_returns_false_when_npmrc_differs():
    file_contents = {
        "package.json": '{"name": "test"}',
        ".npmrc": "//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
    }

    def open_side_effect(path, *_args, **_kwargs):
        for filename, content in file_contents.items():
            if filename in path:
                return mock_open(read_data=content)()
        return mock_open(read_data="")()

    with patch("services.node.install_node_packages.os.path.exists", return_value=True):
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            with patch("builtins.open", side_effect=open_side_effect):
                result = _can_reuse_packages(
                    "/mnt/efs/owner/repo",
                    '{"name": "test"}',
                    "//different-registry.npmjs.org/:_authToken=${NPM_TOKEN}",
                )

                assert result is False


def test_can_reuse_packages_returns_false_when_npmrc_missing_on_efs():
    def exists_side_effect(path):
        if ".npmrc" in path:
            return False
        return True

    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.side_effect = exists_side_effect
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            with patch("builtins.open", mock_open(read_data='{"name": "test"}')):
                result = _can_reuse_packages(
                    "/mnt/efs/owner/repo",
                    '{"name": "test"}',
                    "//registry.npmjs.org/:_authToken=${NPM_TOKEN}",
                )

                assert result is False


@pytest.mark.asyncio
async def test_install_node_packages_returns_false_when_no_package_json():
    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        mock_get.return_value = None

        result = await install_node_packages(
            owner="owner",
            owner_id=123,
            repo="repo",
            branch="main",
            token="token",
            efs_dir="/mnt/efs/owner/repo",
        )

        assert result is False


@pytest.mark.asyncio
async def test_install_node_packages_reuses_existing_packages():
    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages"
            ) as mock_reuse:
                mock_get.return_value = '{"name": "test"}'
                mock_reuse.return_value = True

                result = await install_node_packages(
                    owner="owner",
                    owner_id=123,
                    repo="repo",
                    branch="main",
                    token="token",
                    efs_dir="/mnt/efs/owner/repo",
                )

                assert result is True


@pytest.mark.asyncio
async def test_install_node_packages_runs_npm_install():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.asyncio.create_subprocess_exec",
                            return_value=mock_process,
                        ) as mock_exec:
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.return_value = '{"name": "test"}'

                                result = await install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                mock_exec.assert_called_once()
                                assert result is True


def test_can_reuse_packages_returns_false_when_no_package_json_file():
    def exists_side_effect(path):
        if "package.json" in path:
            return False
        return True

    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.side_effect = exists_side_effect
        with patch(
            "services.node.install_node_packages.os.listdir", return_value=["eslint"]
        ):
            result = _can_reuse_packages(
                "/mnt/efs/owner/repo",
                '{"name": "test"}',
            )

            assert result is False


def test_can_reuse_packages_returns_false_when_bin_directory_missing():
    def exists_side_effect(path):
        if ".bin" in path:
            return False
        return True

    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.side_effect = exists_side_effect

        result = _can_reuse_packages(
            "/mnt/efs/owner/repo",
            '{"name": "test"}',
        )

        assert result is False


def test_can_reuse_packages_returns_false_when_bin_directory_empty():
    with patch("services.node.install_node_packages.os.path.exists", return_value=True):
        with patch("services.node.install_node_packages.os.listdir", return_value=[]):
            result = _can_reuse_packages(
                "/mnt/efs/owner/repo",
                '{"name": "test"}',
            )

            assert result is False


@pytest.mark.asyncio
async def test_install_node_packages_reuses_after_lock():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages"
            ) as mock_reuse:
                mock_reuse.side_effect = [False, True]
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        mock_get.return_value = '{"name": "test"}'

                        result = await install_node_packages(
                            owner="owner",
                            owner_id=123,
                            repo="repo",
                            branch="main",
                            token="token",
                            efs_dir="/mnt/efs/owner/repo",
                        )

                        assert result is True
                        assert mock_reuse.call_count == 2


@pytest.mark.asyncio
async def test_install_node_packages_uses_npm_token():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.asyncio.create_subprocess_exec",
                            return_value=mock_process,
                        ) as mock_exec:
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value="npm_secret_token",
                            ):
                                mock_get.return_value = '{"name": "test"}'

                                result = await install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                call_kwargs = mock_exec.call_args[1]
                                assert "NPM_TOKEN" in call_kwargs["env"]
                                assert (
                                    call_kwargs["env"]["NPM_TOKEN"]
                                    == "npm_secret_token"
                                )
                                assert result is True


@pytest.mark.asyncio
async def test_install_node_packages_sanitizes_http_to_https_in_npmrc():
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    written_content = {}

    def mock_open_side_effect(path, *_args, **_kwargs):
        mock_file = MagicMock()
        mock_file.fileno.return_value = 1
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        def write_side_effect(content):
            written_content[path] = content

        mock_file.write = MagicMock(side_effect=write_side_effect)
        return mock_file

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", side_effect=mock_open_side_effect):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.asyncio.create_subprocess_exec",
                            return_value=mock_process,
                        ):
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.side_effect = [
                                    '{"name": "test"}',
                                    "registry=http://registry.npmjs.org/",
                                    None,
                                    None,
                                ]

                                await install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                npmrc_path = "/mnt/efs/owner/repo/.npmrc"
                                assert npmrc_path in written_content
                                assert (
                                    written_content[npmrc_path]
                                    == "registry=https://registry.npmjs.org/"
                                )


@pytest.mark.asyncio
async def test_install_node_packages_preserves_https_in_npmrc():
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    written_content = {}

    def mock_open_side_effect(path, *_args, **_kwargs):
        mock_file = MagicMock()
        mock_file.fileno.return_value = 1
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        def write_side_effect(content):
            written_content[path] = content

        mock_file.write = MagicMock(side_effect=write_side_effect)
        return mock_file

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", side_effect=mock_open_side_effect):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.asyncio.create_subprocess_exec",
                            return_value=mock_process,
                        ):
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.side_effect = [
                                    '{"name": "test"}',
                                    "registry=https://registry.npmjs.org/",
                                    None,
                                    None,
                                ]

                                await install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                npmrc_path = "/mnt/efs/owner/repo/.npmrc"
                                assert npmrc_path in written_content
                                assert (
                                    written_content[npmrc_path]
                                    == "registry=https://registry.npmjs.org/"
                                )


@pytest.mark.asyncio
async def test_install_node_packages_handles_npm_failure():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"npm ERR!", b""))

    with patch("services.node.install_node_packages.read_file_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.asyncio.create_subprocess_exec",
                            return_value=mock_process,
                        ):
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.return_value = '{"name": "test"}'

                                result = await install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                assert result is False

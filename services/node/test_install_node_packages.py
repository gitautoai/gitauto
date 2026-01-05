from unittest.mock import MagicMock, mock_open, patch

from services.node.install_node_packages import (
    _can_reuse_packages,
    install_node_packages,
)


def test_can_reuse_packages_returns_false_when_no_node_modules():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.return_value = False

        result = _can_reuse_packages("/mnt/efs/owner/repo", "package.json", "{}")

        assert result is False


def test_can_reuse_packages_returns_true_when_content_matches():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data='{"name": "test"}')):
            result = _can_reuse_packages(
                "/mnt/efs/owner/repo",
                "/mnt/efs/owner/repo/package.json",
                '{"name": "test"}',
            )

            assert result is True


def test_can_reuse_packages_returns_false_when_content_differs():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data='{"name": "old"}')):
            result = _can_reuse_packages(
                "/mnt/efs/owner/repo",
                "/mnt/efs/owner/repo/package.json",
                '{"name": "new"}',
            )

            assert result is False


def test_install_node_packages_returns_false_when_no_package_json():
    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        mock_get.return_value = None

        result = install_node_packages(
            owner="owner",
            owner_id=123,
            repo="repo",
            branch="main",
            token="token",
            efs_dir="/mnt/efs/owner/repo",
        )

        assert result is False


def test_install_node_packages_reuses_existing_packages():
    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages"
            ) as mock_reuse:
                mock_get.return_value = '{"name": "test"}'
                mock_reuse.return_value = True

                result = install_node_packages(
                    owner="owner",
                    owner_id=123,
                    repo="repo",
                    branch="main",
                    token="token",
                    efs_dir="/mnt/efs/owner/repo",
                )

                assert result is True


def test_install_node_packages_runs_npm_install():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.subprocess.run"
                        ) as mock_run:
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.return_value = '{"name": "test"}'
                                mock_run.return_value = MagicMock(returncode=0)

                                result = install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                mock_run.assert_called_once()
                                assert result is True


def test_can_reuse_packages_returns_false_when_no_package_json_file():
    with patch("services.node.install_node_packages.os.path.exists") as mock_exists:
        mock_exists.side_effect = [True, False]

        result = _can_reuse_packages(
            "/mnt/efs/owner/repo",
            "/mnt/efs/owner/repo/package.json",
            '{"name": "test"}',
        )

        assert result is False


def test_install_node_packages_reuses_after_lock():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages"
            ) as mock_reuse:
                mock_reuse.side_effect = [False, True]
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        mock_get.return_value = '{"name": "test"}'

                        result = install_node_packages(
                            owner="owner",
                            owner_id=123,
                            repo="repo",
                            branch="main",
                            token="token",
                            efs_dir="/mnt/efs/owner/repo",
                        )

                        assert result is True
                        assert mock_reuse.call_count == 2


def test_install_node_packages_uses_npm_token():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.subprocess.run"
                        ) as mock_run:
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value="npm_secret_token",
                            ):
                                mock_get.return_value = '{"name": "test"}'
                                mock_run.return_value = MagicMock(returncode=0)

                                result = install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                call_kwargs = mock_run.call_args[1]
                                assert "NPM_TOKEN" in call_kwargs["env"]
                                assert (
                                    call_kwargs["env"]["NPM_TOKEN"]
                                    == "npm_secret_token"
                                )
                                assert result is True


def test_install_node_packages_handles_npm_failure():
    mock_lock_file = MagicMock()
    mock_lock_file.fileno.return_value = 1

    with patch("services.node.install_node_packages.get_raw_content") as mock_get:
        with patch("services.node.install_node_packages.os.makedirs"):
            with patch(
                "services.node.install_node_packages._can_reuse_packages",
                return_value=False,
            ):
                with patch("builtins.open", return_value=mock_lock_file):
                    with patch("services.node.install_node_packages.fcntl.flock"):
                        with patch(
                            "services.node.install_node_packages.subprocess.run"
                        ) as mock_run:
                            with patch(
                                "services.node.install_node_packages.get_npm_token",
                                return_value=None,
                            ):
                                mock_get.return_value = '{"name": "test"}'
                                mock_run.return_value = MagicMock(
                                    returncode=1, stderr="npm ERR!"
                                )

                                result = install_node_packages(
                                    owner="owner",
                                    owner_id=123,
                                    repo="repo",
                                    branch="main",
                                    token="token",
                                    efs_dir="/mnt/efs/owner/repo",
                                )

                                assert result is False

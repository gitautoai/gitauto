import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from services.git.clone_repo import clone_repo


@pytest.mark.asyncio
async def test_clone_repo_with_pr_number(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ):
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink"):
                mock_exists.return_value = False

                result = await clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=123,
                    branch="main",
                    token=test_token,
                )

                assert result == f"/tmp/{test_owner}/{test_repo}/pr-123"


@pytest.mark.asyncio
async def test_clone_repo_without_pr_number(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ):
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink"):
                mock_exists.return_value = False

                result = await clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=None,
                    branch="main",
                    token=test_token,
                )

                assert result == f"/tmp/{test_owner}/{test_repo}"


@pytest.mark.asyncio
async def test_clone_repo_reuses_existing_dir(test_owner, test_repo, test_token):
    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec"
    ) as mock_subprocess:
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            mock_exists.return_value = True

            result = await clone_repo(
                owner=test_owner,
                repo=test_repo,
                pr_number=456,
                branch="main",
                token=test_token,
            )

            assert result == f"/tmp/{test_owner}/{test_repo}/pr-456"
            mock_subprocess.assert_not_called()


@pytest.mark.asyncio
async def test_clone_repo_symlinks_node_modules(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ):
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink") as mock_symlink:
                with patch("services.git.clone_repo.get_efs_dir") as mock_efs:
                    mock_efs.return_value = f"/mnt/efs/{test_owner}/{test_repo}"

                    def exists_side_effect(path):
                        if "pr-789" in path:
                            return False
                        if "efs" in path and "node_modules" in path:
                            return True
                        return False

                    mock_exists.side_effect = exists_side_effect

                    await clone_repo(
                        owner=test_owner,
                        repo=test_repo,
                        pr_number=789,
                        branch="feature",
                        token=test_token,
                    )

                    mock_symlink.assert_called_once_with(
                        f"/mnt/efs/{test_owner}/{test_repo}/node_modules",
                        f"/tmp/{test_owner}/{test_repo}/pr-789/node_modules",
                    )


@pytest.mark.asyncio
async def test_clone_repo_uses_shallow_clone(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ) as mock_subprocess:
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            with patch("services.git.clone_repo.os.symlink"):
                await clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="develop",
                    token=test_token,
                )

                call_args = mock_subprocess.call_args[0]
                assert "--depth" in call_args
                assert "1" in call_args
                assert "--branch" in call_args
                assert "develop" in call_args


@pytest.mark.asyncio
async def test_clone_repo_subprocess_error(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(
        return_value=(b"", b"fatal: repository not found")
    )

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ):
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="git clone failed"):
                await clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="main",
                    token=test_token,
                )


@pytest.mark.asyncio
async def test_clone_repo_timeout(test_owner, test_repo, test_token):
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch(
        "services.git.clone_repo.asyncio.create_subprocess_exec",
        return_value=mock_process,
    ):
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            with pytest.raises(asyncio.TimeoutError):
                await clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="main",
                    token=test_token,
                )

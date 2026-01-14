import subprocess
from unittest.mock import patch, MagicMock

import pytest

from services.git.clone_repo import clone_repo


def test_clone_repo_with_pr_number(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink"):
                mock_run.return_value = MagicMock(returncode=0)
                mock_exists.return_value = False

                result = clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=123,
                    branch="main",
                    token=test_token,
                )

                assert result == f"/tmp/{test_owner}/{test_repo}/pr-123"


def test_clone_repo_without_pr_number(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink"):
                mock_run.return_value = MagicMock(returncode=0)
                mock_exists.return_value = False

                result = clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=None,
                    branch="main",
                    token=test_token,
                )

                assert result == f"/tmp/{test_owner}/{test_repo}"


def test_clone_repo_reuses_existing_dir(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            mock_exists.return_value = True

            result = clone_repo(
                owner=test_owner,
                repo=test_repo,
                pr_number=456,
                branch="main",
                token=test_token,
            )

            assert result == f"/tmp/{test_owner}/{test_repo}/pr-456"
            mock_run.assert_not_called()


def test_clone_repo_symlinks_node_modules(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists") as mock_exists:
            with patch("services.git.clone_repo.os.symlink") as mock_symlink:
                with patch("services.git.clone_repo.get_efs_dir") as mock_efs:
                    mock_run.return_value = MagicMock(returncode=0)
                    mock_efs.return_value = f"/mnt/efs/{test_owner}/{test_repo}"

                    def exists_side_effect(path):
                        if "pr-789" in path:
                            return False
                        if "efs" in path and "node_modules" in path:
                            return True
                        return False

                    mock_exists.side_effect = exists_side_effect

                    clone_repo(
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


def test_clone_repo_uses_shallow_clone(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            with patch("services.git.clone_repo.os.symlink"):
                mock_run.return_value = MagicMock(returncode=0)

                clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="develop",
                    token=test_token,
                )

                clone_call = mock_run.call_args_list[0]
                clone_cmd = clone_call[0][0]
                assert "--depth" in clone_cmd
                assert "1" in clone_cmd
                assert "--branch" in clone_cmd
                assert "develop" in clone_cmd


def test_clone_repo_subprocess_error(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="git clone",
                stderr="fatal: repository not found",
            )

            with pytest.raises(subprocess.CalledProcessError):
                clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="main",
                    token=test_token,
                )


def test_clone_repo_timeout(test_owner, test_repo, test_token):
    with patch("services.git.clone_repo.subprocess.run") as mock_run:
        with patch("services.git.clone_repo.os.path.exists", return_value=False):
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd="git clone", timeout=180
            )

            with pytest.raises(subprocess.TimeoutExpired):
                clone_repo(
                    owner=test_owner,
                    repo=test_repo,
                    pr_number=100,
                    branch="main",
                    token=test_token,
                )

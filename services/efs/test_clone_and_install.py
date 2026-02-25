# pylint: disable=redefined-outer-name
# pyright: reportUnusedVariable=false
from unittest.mock import AsyncMock, patch

import pytest

from services.efs.clone_and_install import clone_and_install


@pytest.fixture
def mock_installation():
    return {
        "installation_id": 12345,
        "owner_id": 789,
        "owner_name": "test-owner",
    }


@pytest.fixture
def mock_repository():
    return {
        "repo_id": 123456,
        "repo_name": "test-repo",
        "owner_id": 789,
        "target_branch": "develop",
    }


@pytest.mark.asyncio
@patch("services.efs.clone_and_install.set_trigger")
@patch("services.efs.clone_and_install.set_owner_repo")
@patch("services.efs.clone_and_install.get_installation_by_owner")
async def test_clone_and_install_no_installation(
    mock_get_installation,
    _mock_set_owner_repo,
    _mock_set_trigger,
):
    mock_get_installation.return_value = None

    result = await clone_and_install("nonexistent-owner", "test-repo")

    assert result.status == "error"
    assert "No installation found" in result.message


@pytest.mark.asyncio
@patch("services.efs.clone_and_install.set_trigger")
@patch("services.efs.clone_and_install.set_owner_repo")
@patch("services.efs.clone_and_install.ensure_php_packages", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.ensure_node_packages", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.get_clone_url")
@patch("services.efs.clone_and_install.get_efs_dir")
@patch("services.efs.clone_and_install.get_repository_by_name")
@patch("services.efs.clone_and_install.get_installation_access_token")
@patch("services.efs.clone_and_install.get_installation_by_owner")
async def test_clone_and_install_with_target_branch(
    mock_get_installation,
    mock_get_token,
    mock_get_repo,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_clone,
    mock_install_node,
    mock_install_php,
    _mock_set_owner_repo,
    _mock_set_trigger,
    mock_installation,
    mock_repository,
):
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_get_repo.return_value = mock_repository
    mock_get_efs_dir.return_value = "/mnt/efs/test-owner/test-repo"
    mock_get_clone_url.return_value = "https://github.com/test-owner/test-repo.git"
    mock_install_node.return_value = True
    mock_install_php.return_value = False

    result = await clone_and_install("test-owner", "test-repo")

    assert result.status == "success"
    assert result.efs_dir == "/mnt/efs/test-owner/test-repo"
    assert result.node_installed is True
    assert result.php_installed is False

    mock_git_clone.assert_called_once_with(
        "/mnt/efs/test-owner/test-repo",
        "https://github.com/test-owner/test-repo.git",
        "develop",
    )


@pytest.mark.asyncio
@patch("services.efs.clone_and_install.set_trigger")
@patch("services.efs.clone_and_install.set_owner_repo")
@patch("services.efs.clone_and_install.ensure_php_packages", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.ensure_node_packages", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.git_clone_to_efs", new_callable=AsyncMock)
@patch("services.efs.clone_and_install.get_clone_url")
@patch("services.efs.clone_and_install.get_efs_dir")
@patch("services.efs.clone_and_install.get_default_branch")
@patch("services.efs.clone_and_install.get_repository_by_name")
@patch("services.efs.clone_and_install.get_installation_access_token")
@patch("services.efs.clone_and_install.get_installation_by_owner")
async def test_clone_and_install_with_default_branch(
    mock_get_installation,
    mock_get_token,
    mock_get_repo,
    mock_get_default_branch,
    mock_get_efs_dir,
    mock_get_clone_url,
    mock_git_clone,
    mock_install_node,
    mock_install_php,
    _mock_set_owner_repo,
    _mock_set_trigger,
    mock_installation,
):
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_get_repo.return_value = None
    mock_get_default_branch.return_value = ("main", False)
    mock_get_efs_dir.return_value = "/mnt/efs/test-owner/test-repo"
    mock_get_clone_url.return_value = "https://github.com/test-owner/test-repo.git"
    mock_install_node.return_value = True
    mock_install_php.return_value = False

    result = await clone_and_install("test-owner", "test-repo")

    assert result.status == "success"
    mock_get_default_branch.assert_called_once_with(
        owner="test-owner", repo="test-repo", token="test-token"
    )
    mock_git_clone.assert_called_once_with(
        "/mnt/efs/test-owner/test-repo",
        "https://github.com/test-owner/test-repo.git",
        "main",
    )


@pytest.mark.asyncio
@patch("services.efs.clone_and_install.set_trigger")
@patch("services.efs.clone_and_install.set_owner_repo")
@patch("services.efs.clone_and_install.get_default_branch")
@patch("services.efs.clone_and_install.get_repository_by_name")
@patch("services.efs.clone_and_install.get_installation_access_token")
@patch("services.efs.clone_and_install.get_installation_by_owner")
async def test_clone_and_install_empty_repository(
    mock_get_installation,
    mock_get_token,
    mock_get_repo,
    mock_get_default_branch,
    _mock_set_owner_repo,
    _mock_set_trigger,
    mock_installation,
):
    mock_get_installation.return_value = mock_installation
    mock_get_token.return_value = "test-token"
    mock_get_repo.return_value = None
    mock_get_default_branch.return_value = ("", True)

    result = await clone_and_install("test-owner", "test-repo")

    assert result.status == "error"
    assert "Repository is empty" in result.message

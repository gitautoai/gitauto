import asyncio
from unittest.mock import patch

import pytest

from services.efs.is_efs_install_ready import is_efs_install_ready


@pytest.mark.asyncio
async def test_is_efs_install_ready_returns_true_when_install_succeeds():
    async def coro():
        return True

    task = asyncio.create_task(coro())
    await task

    with patch(
        "services.efs.is_efs_install_ready.install_tasks",
        {"/mnt/efs/owner/repo": {"node": task}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = await is_efs_install_ready("owner", "repo", "node")

    assert result is True


@pytest.mark.asyncio
async def test_is_efs_install_ready_returns_false_when_install_fails():
    async def coro():
        return False

    task = asyncio.create_task(coro())
    await task

    with patch(
        "services.efs.is_efs_install_ready.install_tasks",
        {"/mnt/efs/owner/repo": {"node": task}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = await is_efs_install_ready("owner", "repo", "node")

    assert result is False


@pytest.mark.asyncio
async def test_is_efs_install_ready_returns_false_when_no_task():
    with patch("services.efs.is_efs_install_ready.install_tasks", {}):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = await is_efs_install_ready("owner", "repo", "node")

    assert result is False


@pytest.mark.asyncio
async def test_is_efs_install_ready_returns_false_when_wrong_installer():
    async def coro():
        return True

    task = asyncio.create_task(coro())
    await task

    with patch(
        "services.efs.is_efs_install_ready.install_tasks",
        {"/mnt/efs/owner/repo": {"python": task}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = await is_efs_install_ready("owner", "repo", "node")

    assert result is False


@pytest.mark.asyncio
async def test_is_efs_install_ready_uses_default_name():
    async def coro():
        return True

    task = asyncio.create_task(coro())
    await task

    with patch(
        "services.efs.is_efs_install_ready.install_tasks",
        {"/mnt/efs/owner/repo": {"node": task}},
    ):
        with patch(
            "services.efs.is_efs_install_ready.get_efs_dir",
            return_value="/mnt/efs/owner/repo",
        ):
            result = await is_efs_install_ready("owner", "repo")

    assert result is True

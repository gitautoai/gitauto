# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import asyncio
from collections import defaultdict
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from services.efs.start_async_install_on_efs import start_async_install_on_efs
from services.github.types.github_types import BaseArgs


def create_mock_create_task(mock_task):
    def side_effect(coro):
        coro.close()
        return mock_task

    return side_effect


@pytest.mark.asyncio
async def test_start_async_install_on_efs_creates_install_task():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    mock_task = MagicMock(spec=asyncio.Task)
    mock_task.done.return_value = False

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task",
        side_effect=create_mock_create_task(mock_task),
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            defaultdict(dict),
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_start_async_install_on_efs_reuses_successful_tasks():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    existing_install_task = MagicMock(spec=asyncio.Task)
    existing_install_task.done.return_value = True
    existing_install_task.exception.return_value = None
    existing_install_task.result.return_value = True

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task"
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            {"/mnt/efs/test-owner/test-repo": {"node": existing_install_task}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_start_async_install_on_efs_retries_failed_install_task():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    failed_install_task = MagicMock(spec=asyncio.Task)
    failed_install_task.done.return_value = True
    failed_install_task.exception.return_value = None
    failed_install_task.result.return_value = False

    new_task = MagicMock(spec=asyncio.Task)
    mock_install_tasks = {
        "/mnt/efs/test-owner/test-repo": {"node": failed_install_task}
    }

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task",
        side_effect=create_mock_create_task(new_task),
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            mock_install_tasks,
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_start_async_install_on_efs_skips_in_progress_tasks():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    in_progress_install_task = MagicMock(spec=asyncio.Task)
    in_progress_install_task.done.return_value = False

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task"
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            {"/mnt/efs/test-owner/test-repo": {"node": in_progress_install_task}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_not_called()

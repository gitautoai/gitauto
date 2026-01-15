import asyncio
from collections import defaultdict
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from services.efs.start_async_install_on_efs import start_async_install_on_efs
from services.github.types.github_types import BaseArgs


@pytest.mark.asyncio
async def test_start_async_install_on_efs_creates_task():
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
        return_value=mock_task,
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
async def test_start_async_install_on_efs_reuses_successful_task():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    existing_task = MagicMock(spec=asyncio.Task)
    existing_task.done.return_value = True
    existing_task.result.return_value = True

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task"
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            {"/mnt/efs/test-owner/test-repo": {"node": existing_task}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_start_async_install_on_efs_retries_failed_task():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    failed_task = MagicMock(spec=asyncio.Task)
    failed_task.done.return_value = True
    failed_task.result.return_value = False

    new_task = MagicMock(spec=asyncio.Task)
    mock_tasks = {"/mnt/efs/test-owner/test-repo": {"node": failed_task}}

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task",
        return_value=new_task,
    ) as mock_create:
        with patch("services.efs.start_async_install_on_efs.install_tasks", mock_tasks):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_start_async_install_on_efs_skips_in_progress_task():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "base_branch": "test-branch",
    }

    in_progress_task = MagicMock(spec=asyncio.Task)
    in_progress_task.done.return_value = False

    with patch(
        "services.efs.start_async_install_on_efs.asyncio.create_task"
    ) as mock_create:
        with patch(
            "services.efs.start_async_install_on_efs.install_tasks",
            {"/mnt/efs/test-owner/test-repo": {"node": in_progress_task}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_create.assert_not_called()

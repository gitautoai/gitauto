from collections import defaultdict
from concurrent.futures import Future
from typing import cast
from unittest.mock import MagicMock, patch

from services.efs.start_async_install_on_efs import start_async_install_on_efs
from services.github.types.github_types import BaseArgs


def test_start_async_install_on_efs_submits_future():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
    }

    mock_executor = MagicMock()
    mock_future = Future()
    mock_executor.submit.return_value = mock_future

    with patch("services.efs.start_async_install_on_efs._executor", mock_executor):
        with patch(
            "services.efs.start_async_install_on_efs.install_futures",
            defaultdict(dict),
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_executor.submit.assert_called_once()


def test_start_async_install_on_efs_reuses_successful_future():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
    }

    existing_future = Future()
    existing_future.set_result(True)

    mock_executor = MagicMock()

    with patch("services.efs.start_async_install_on_efs._executor", mock_executor):
        with patch(
            "services.efs.start_async_install_on_efs.install_futures",
            {"/mnt/efs/test-owner/test-repo": {"node": existing_future}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_executor.submit.assert_not_called()


def test_start_async_install_on_efs_retries_failed_future():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
    }

    failed_future = Future()
    failed_future.set_result(False)

    mock_executor = MagicMock()
    new_future = Future()
    mock_executor.submit.return_value = new_future

    mock_futures = {"/mnt/efs/test-owner/test-repo": {"node": failed_future}}

    with patch("services.efs.start_async_install_on_efs._executor", mock_executor):
        with patch(
            "services.efs.start_async_install_on_efs.install_futures", mock_futures
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_executor.submit.assert_called_once()


def test_start_async_install_on_efs_skips_in_progress_future():
    base_args = {
        "owner": "test-owner",
        "owner_id": 12345,
        "repo": "test-repo",
        "token": "test-token",
        "new_branch": "test-branch",
    }

    in_progress_future = Future()

    mock_executor = MagicMock()

    with patch("services.efs.start_async_install_on_efs._executor", mock_executor):
        with patch(
            "services.efs.start_async_install_on_efs.install_futures",
            {"/mnt/efs/test-owner/test-repo": {"node": in_progress_future}},
        ):
            with patch(
                "services.efs.start_async_install_on_efs.get_efs_dir",
                return_value="/mnt/efs/test-owner/test-repo",
            ):
                start_async_install_on_efs(cast(BaseArgs, base_args))

    mock_executor.submit.assert_not_called()

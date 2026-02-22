import asyncio
import os
import time
from unittest.mock import patch

import pytest

from services.git.remove_stale_git_locks import (
    STALE_LOCK_SECONDS,
    remove_stale_git_locks,
)
from services.git.wait_for_git_locks import wait_for_git_locks


def test_removes_stale_shallow_lock(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    remove_stale_git_locks(str(git_dir))

    assert not lock_file.exists()


def test_removes_stale_index_lock(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "index.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    remove_stale_git_locks(str(git_dir))

    assert not lock_file.exists()


def test_removes_stale_lock_in_subdirectory(tmp_path):
    git_dir = tmp_path / ".git"
    refs_dir = git_dir / "refs" / "heads"
    refs_dir.mkdir(parents=True)
    lock_file = refs_dir / "main.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    remove_stale_git_locks(str(git_dir))

    assert not lock_file.exists()


def test_preserves_fresh_lock(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()
    # Fresh lock — just created, mtime is now

    remove_stale_git_locks(str(git_dir))

    assert lock_file.exists()


def test_preserves_non_lock_files(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text("normal file")
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(config, (stale_mtime, stale_mtime))

    remove_stale_git_locks(str(git_dir))

    assert config.exists()


def test_handles_lock_deleted_between_walk_and_stat(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()

    # Simulate lock disappearing between os.walk and os.path.getmtime
    original_getmtime = os.path.getmtime

    def getmtime_raises(path):
        if str(path).endswith(".lock"):
            raise FileNotFoundError
        return original_getmtime(path)

    with patch(
        "services.git.remove_stale_git_locks.time.time", return_value=time.time()
    ):
        with patch(
            "services.git.remove_stale_git_locks.os.path.getmtime",
            side_effect=getmtime_raises,
        ):
            remove_stale_git_locks(str(git_dir))
    # Should not raise


def test_no_error_on_empty_git_dir(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    remove_stale_git_locks(str(git_dir))
    # Should not raise


@pytest.mark.asyncio
async def test_wait_for_git_locks_returns_immediately_when_no_locks(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    await wait_for_git_locks(str(git_dir))
    # Should return immediately


@pytest.mark.asyncio
async def test_wait_for_git_locks_waits_for_lock_release(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()

    async def remove_lock_after_delay():
        await asyncio.sleep(0.5)
        lock_file.unlink()

    asyncio.create_task(remove_lock_after_delay())

    with patch("services.git.wait_for_git_locks.LOCK_POLL_INTERVAL", 0.2):
        await wait_for_git_locks(str(git_dir))

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_wait_for_git_locks_force_removes_on_timeout(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()

    with patch("services.git.wait_for_git_locks.LOCK_POLL_INTERVAL", 0.1), patch(
        "services.git.wait_for_git_locks.LOCK_WAIT_TIMEOUT", 0.3
    ):
        await wait_for_git_locks(str(git_dir))

    assert not lock_file.exists()

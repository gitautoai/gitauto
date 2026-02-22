import asyncio
import os
import time
from unittest.mock import patch

import pytest

from services.git.resolve_git_locks import (
    STALE_LOCK_SECONDS,
    resolve_git_locks,
)


@pytest.mark.asyncio
async def test_removes_stale_shallow_lock(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    await resolve_git_locks(str(git_dir))

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_removes_stale_index_lock(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "index.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    await resolve_git_locks(str(git_dir))

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_removes_stale_lock_in_subdirectory(tmp_path):
    git_dir = tmp_path / ".git"
    refs_dir = git_dir / "refs" / "heads"
    refs_dir.mkdir(parents=True)
    lock_file = refs_dir / "main.lock"
    lock_file.touch()
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(lock_file, (stale_mtime, stale_mtime))

    await resolve_git_locks(str(git_dir))

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_preserves_non_lock_files(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text("normal file")
    stale_mtime = time.time() - STALE_LOCK_SECONDS - 1
    os.utime(config, (stale_mtime, stale_mtime))

    await resolve_git_locks(str(git_dir))

    assert config.exists()


@pytest.mark.asyncio
async def test_no_locks_returns_immediately(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    await resolve_git_locks(str(git_dir))


@pytest.mark.asyncio
async def test_waits_for_fresh_lock_release(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()

    async def remove_lock_after_delay():
        await asyncio.sleep(0.5)
        lock_file.unlink()

    asyncio.create_task(remove_lock_after_delay())

    with patch("services.git.resolve_git_locks.LOCK_POLL_INTERVAL", 0.2):
        await resolve_git_locks(str(git_dir))

    assert not lock_file.exists()


@pytest.mark.asyncio
async def test_force_removes_fresh_lock_on_timeout(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    lock_file = git_dir / "shallow.lock"
    lock_file.touch()

    with patch("services.git.resolve_git_locks.LOCK_POLL_INTERVAL", 0.1), patch(
        "services.git.resolve_git_locks.LOCK_WAIT_TIMEOUT", 0.3
    ):
        await resolve_git_locks(str(git_dir))

    assert not lock_file.exists()

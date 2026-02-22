import asyncio
import os
import time

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

LOCK_POLL_INTERVAL = 2  # seconds between polls
LOCK_WAIT_TIMEOUT = 60  # max seconds to wait for a fresh lock


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def wait_for_git_locks(git_dir: str):
    """Wait for active git lock files to be released by another process."""
    deadline = time.time() + LOCK_WAIT_TIMEOUT
    while time.time() < deadline:
        lock_files = [
            os.path.join(root, f)
            for root, _, files in os.walk(git_dir)
            for f in files
            if f.endswith(".lock")
        ]
        if not lock_files:
            return
        logger.info(
            "Waiting for git locks: %s", [os.path.basename(f) for f in lock_files]
        )
        await asyncio.sleep(LOCK_POLL_INTERVAL)

    # Timeout - force remove remaining locks so we don't hang forever
    for root, _, files in os.walk(git_dir):
        for fname in files:
            if not fname.endswith(".lock"):
                continue
            lock_path = os.path.join(root, fname)
            try:
                os.remove(lock_path)
                logger.warning(
                    "Force-removed lock after %ds timeout: %s",
                    LOCK_WAIT_TIMEOUT,
                    lock_path,
                )
            except FileNotFoundError:
                pass

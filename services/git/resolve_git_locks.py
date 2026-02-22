import asyncio
import os
import time

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

STALE_LOCK_SECONDS = 600  # 10 minutes — matches Lambda max timeout
LOCK_POLL_INTERVAL = 2  # seconds between polls
LOCK_WAIT_TIMEOUT = 60  # max seconds to wait for a fresh lock


@handle_exceptions(default_return_value=None, raise_on_error=False)
async def resolve_git_locks(git_dir: str):
    """Clear git lock files: remove stale ones immediately, wait for fresh ones.

    - Lock >10min old (crashed Lambda): remove immediately
    - Lock fresh (concurrent Lambda): poll every 2s up to 60s, force-remove on timeout
    """
    deadline = time.time() + LOCK_WAIT_TIMEOUT
    while time.time() < deadline:
        has_fresh_locks = False
        for root, _, files in os.walk(git_dir):
            for fname in files:
                if not fname.endswith(".lock"):
                    continue

                lock_path = os.path.join(root, fname)
                try:
                    age = time.time() - os.path.getmtime(lock_path)
                except FileNotFoundError:
                    continue  # Lock was released between walk and stat

                if age > STALE_LOCK_SECONDS:
                    try:
                        os.remove(lock_path)
                        logger.info(
                            "Removed stale %s (%.0fs old): %s", fname, age, lock_path
                        )
                    except FileNotFoundError:
                        pass
                else:
                    has_fresh_locks = True

        if not has_fresh_locks:
            return

        logger.info("Waiting for fresh git locks in %s", git_dir)
        await asyncio.sleep(LOCK_POLL_INTERVAL)

    # Timeout - force remove remaining locks
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

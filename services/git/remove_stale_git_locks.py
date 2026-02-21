import os
import time

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

STALE_LOCK_SECONDS = 600  # 10 minutes — matches Lambda max timeout


@handle_exceptions(default_return_value=None, raise_on_error=False)
def remove_stale_git_locks(git_dir: str):
    """Remove *.lock files left by killed Lambda invocations.

    EFS persists across invocations, so a Lambda killed mid-fetch/reset leaves
    lock files (shallow.lock, index.lock, config.lock, etc.) that block all
    subsequent git operations on the same repo.
    """
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
                    pass  # Lock was released between stat and remove

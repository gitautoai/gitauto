"""Clean up /tmp at the start of each Lambda invocation.

Lambda containers handle ONE request at a time. When a new request starts on a warm
container, the previous request has already finished. So we can safely delete all
PR folders from /tmp to prevent /tmp filling up (10GB limit).

Why at START, not END: If Lambda times out or crashes (OOM), cleanup at END won't run.
Cleanup at START guarantees it runs regardless of how the previous invocation ended.
"""

import os
import shutil

from utils.logging.logging_config import logger

TMP_DIR = "/tmp"


def cleanup_tmp():
    """Delete all owner/repo folders from /tmp.

    Safe to call at invocation start because Lambda containers handle one request
    at a time - any previous request has already finished.
    """
    # Only run on Lambda - local /tmp is shared by all processes
    if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return

    if not os.path.exists(TMP_DIR):
        return

    deleted_count = 0
    deleted_bytes = 0

    # /tmp/{owner}/{repo}/pr-{number} structure
    # We delete at the owner level to clean everything
    for item in os.listdir(TMP_DIR):
        item_path = os.path.join(TMP_DIR, item)

        # Skip non-directories and system files
        if not os.path.isdir(item_path):
            continue

        # Skip common system/tool directories that shouldn't be deleted
        if item.startswith(".") or item in ("pip", "npm", "yarn", "cache"):
            continue

        # This is likely an owner directory (e.g., /tmp/Foxquilt)
        # Calculate size before deleting
        try:
            for dirpath, _, filenames in os.walk(item_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        deleted_bytes += os.path.getsize(filepath)
                    except OSError:
                        pass

            shutil.rmtree(item_path)
            deleted_count += 1
        except OSError as e:
            logger.warning("Failed to delete %s: %s", item_path, e)

    if deleted_count > 0:
        deleted_mb = deleted_bytes / (1024 * 1024)
        logger.info(
            "Cleaned /tmp: deleted %d folders (%.1f MB)", deleted_count, deleted_mb
        )

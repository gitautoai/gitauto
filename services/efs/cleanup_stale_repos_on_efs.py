import os
import shutil
import time

from services.slack.slack_notify import slack_notify
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger, set_trigger

STALE_DAYS = 30
STALE_SECONDS = STALE_DAYS * 24 * 60 * 60


@handle_exceptions(default_return_value=None, raise_on_error=False)
def cleanup_stale_repos_on_efs(base_dir: str = "/mnt/efs"):
    set_trigger("cleanup_stale_repos")
    if not os.path.exists(base_dir):
        logger.info("Base directory %s does not exist, skipping cleanup", base_dir)
        return {"deleted": 0, "size_freed": 0}

    current_time = int(time.time())
    total_deleted = 0
    total_size_freed = 0
    thread_ts: str | None = None

    for owner in os.listdir(base_dir):
        owner_path = os.path.join(base_dir, owner)
        if not os.path.isdir(owner_path):
            logger.info("Skipping non-directory at owner level: %s", owner_path)
            continue

        for repo in os.listdir(owner_path):
            repo_path = os.path.join(owner_path, repo)
            if not os.path.isdir(repo_path):
                logger.info("Skipping non-directory at repo level: %s", repo_path)
                continue

            try:
                stat_info = os.stat(repo_path)
                last_modified_time = stat_info.st_mtime

                age_seconds = current_time - last_modified_time
                age_days = age_seconds / (24 * 60 * 60)

                if age_seconds > STALE_SECONDS:
                    size_before = _get_dir_size(repo_path)
                    logger.info(
                        "Deleting stale repo on EFS: %s/%s (last modified %.1f days ago, %s)",
                        owner,
                        repo,
                        age_days,
                        _format_size(size_before),
                    )

                    # If Lambda times out (15 mins), completed repo deletions are permanent and next cleanup continues with remaining repos.
                    # Inside a repo, if timeout occurs mid-rmtree, the partially deleted repo will be finished on next cleanup.
                    shutil.rmtree(repo_path)
                    logger.info("Deleted %s/%s", owner, repo)

                    if thread_ts is None:
                        thread_ts = slack_notify("EFS cleanup: found stale repos")
                    slack_notify(
                        f"Deleted {owner}/{repo} ({_format_size(size_before)}, {age_days:.0f} days old)",
                        thread_ts,
                    )
                    total_deleted += 1
                    total_size_freed += size_before
                else:
                    logger.info(
                        "Keeping %s/%s (last modified %.1f days ago)",
                        owner,
                        repo,
                        age_days,
                    )

            except OSError as e:
                logger.error("Failed to process %s/%s: %s", owner, repo, e)
                continue

    logger.info(
        "Cleanup summary: Deleted %d repos on EFS, freed %s",
        total_deleted,
        _format_size(total_size_freed),
    )
    if thread_ts:
        slack_notify(
            f"Completed: Deleted {total_deleted} repos, freed {_format_size(total_size_freed)}",
            thread_ts,
        )

    return {"deleted": total_deleted, "size_freed": total_size_freed}


def _get_dir_size(path: str):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += _get_dir_size(entry.path)
    except PermissionError:
        pass
    return total


def _format_size(size_bytes: float):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def lambda_handler(_event, _context):
    return cleanup_stale_repos_on_efs()

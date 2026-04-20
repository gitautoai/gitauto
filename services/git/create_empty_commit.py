from services.git.get_branch_head_author import get_branch_head_author
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def create_empty_commit(
    base_args: BaseArgs,
    message: str = "Empty commit to trigger final tests",
):
    clone_url = base_args["clone_url"]
    branch = base_args["new_branch"]
    clone_dir = base_args["clone_dir"]
    commit_args = ["git", "commit", "--allow-empty", "--no-verify", "-m", message]
    push_args = ["git", "push", clone_url, f"HEAD:refs/heads/{branch}"]

    # --no-verify skips pre-commit hooks (e.g. lint-staged) that fail in Lambda sandbox because npm can't mkdir /home/sbx_user1051
    run_subprocess(args=commit_args, cwd=clone_dir)
    try:
        run_subprocess(args=push_args, cwd=clone_dir)
    except ValueError as err:
        err_text = str(err)
        if "fetch first" not in err_text and "non-fast-forward" not in err_text:
            logger.error(
                "Empty commit push failed with unhandled error on branch %s: %s",
                branch,
                err_text,
            )
            raise
        author = get_branch_head_author(clone_dir, clone_url, branch)
        logger.warning(
            "create_empty_commit abandoning %s: remote has commits we do not have (racer=%s). Retriggering CI on a state they chose to land is noise; returning False so the caller can post accurate status instead of claiming CI was re-triggered.",
            branch,
            author,
        )
        return False

    logger.info("create_empty_commit pushed on %s", branch)
    return True

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

        # A concurrent handler (e.g. check_suite on an earlier push) landed a commit on this branch while our agent loop was running. Sync local to remote, drop our local empty commit, recreate on top of the new tip, and push. Our real work was already pushed by git_commit_and_push earlier in the flow, so the only local-but-not-remote commit here is the empty one we just made.
        logger.warning(
            "Empty commit push rejected (non-fast-forward); syncing with remote %s and retrying",
            branch,
        )
        run_subprocess(args=["git", "fetch", clone_url, branch], cwd=clone_dir)
        run_subprocess(args=["git", "reset", "--hard", "FETCH_HEAD"], cwd=clone_dir)
        run_subprocess(args=commit_args, cwd=clone_dir)
        run_subprocess(args=push_args, cwd=clone_dir)

    return True

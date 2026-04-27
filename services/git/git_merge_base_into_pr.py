from services.git.deepen_until_merge_base import deepen_until_merge_base
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def git_merge_base_into_pr(clone_dir: str, base_branch: str, behind_by: int):
    # Need a merge-base before merging; see deepen_until_merge_base for the why.
    # When GitHub's Compare API gave us a known behind_by, deepen by that exact amount in one shot — cheaper than the helper's exponential climb.
    # Otherwise fall back to the shared helper.
    if behind_by > 0:
        # behind_by from GitHub Compare API: e.g. PR is 50 commits behind main → deepen 60
        depth = behind_by + 10
        logger.info("Deepening by %d (behind_by=%d + buffer)", depth, behind_by)
        run_subprocess(
            ["git", "fetch", "--deepen", str(depth), "origin", base_branch], clone_dir
        )
    else:
        logger.info(
            "behind_by=0, delegating to deepen_until_merge_base for exponential fallback"
        )
        deepen_until_merge_base(clone_dir, base_branch)

    # Merge base branch into PR branch
    try:
        logger.info("Merging origin/%s into PR branch", base_branch)
        run_subprocess(
            ["git", "merge", f"origin/{base_branch}", "--no-edit"], clone_dir
        )
        logger.info("Clean merge of %s into PR branch", base_branch)
    except ValueError:
        # Merge conflict — markers are in working tree, git is in "merging" state.
        # Commit the markers so git returns to a clean state.
        # The agent can then fix conflict markers file-by-file with its normal tools.
        logger.warning(
            "Merge conflict merging %s into PR branch, committing markers", base_branch
        )
        # Get only the conflicted files (auto-merged files are already staged by git)
        logger.info("Getting conflicted files")
        result = run_subprocess(
            ["git", "diff", "--name-only", "--diff-filter=U"], clone_dir
        )
        conflicted_files = result.stdout.strip().splitlines()
        logger.info("Conflicted files: %s", conflicted_files)
        for f in conflicted_files:
            logger.info("Staging conflicted file: %s", f)
            run_subprocess(["git", "add", f], clone_dir)
        logger.info("Committing conflict markers")
        run_subprocess(
            ["git", "commit", "--no-edit", "-m", f"Merge {base_branch} (conflicts)"],
            clone_dir,
        )

    logger.info("git_merge_base_into_pr completed: %s", clone_dir)
    return True

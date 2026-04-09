from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
def git_merge_base_into_pr(clone_dir: str, base_branch: str, behind_by: int):
    # Shallow clones (--depth 1) lack a common ancestor, so git merge fails.
    # --unshallow fetches full history but is too slow for large repos (e.g. 61K commits = 137s).
    # Instead, --deepen N fetches only N more commits from the shallow boundary.
    if behind_by > 0:
        # behind_by from GitHub Compare API: e.g. PR is 50 commits behind main → deepen 60
        depth = behind_by + 10
        logger.info("Deepening by %d (behind_by=%d + buffer)", depth, behind_by)
        run_subprocess(
            ["git", "fetch", "--deepen", str(depth), "origin", base_branch], clone_dir
        )
    else:
        # API failed (returned default 0) — exponential deepen: 100 → 500 → 2500 → 12500
        logger.info("behind_by=0, using exponential deepen fallback")
        depth = 100
        while depth <= 12500:
            logger.info("Deepening by %d", depth)
            run_subprocess(
                ["git", "fetch", "--deepen", str(depth), "origin", base_branch],
                clone_dir,
            )
            try:
                run_subprocess(
                    ["git", "merge-base", "HEAD", f"origin/{base_branch}"], clone_dir
                )
                logger.info("Merge base found at deepen=%d", depth)
                break
            except ValueError:
                logger.info("Merge base not found at deepen=%d", depth)
                depth *= 5
        else:
            # Cumulative depth after loop: 100+500+2500+12500 = 15600 commits wasn't enough
            logger.warning("Exponential deepen exhausted, falling back to --unshallow")
            run_subprocess(
                ["git", "fetch", "--unshallow", "origin", base_branch], clone_dir
            )

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

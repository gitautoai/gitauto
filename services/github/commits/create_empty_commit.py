# Local imports
from services.github.types.github_types import BaseArgs
from services.github.commits.create_commit import create_commit
from services.github.commits.get_commit import get_commit
from services.github.refs.get_reference import get_reference
from services.github.refs.update_reference import update_reference
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def create_empty_commit(
    base_args: BaseArgs, message: str = "Empty commit to trigger final tests"
):
    # Get current branch reference
    current_sha = get_reference(base_args)
    if not current_sha:
        return False

    # Get current commit to get tree SHA
    tree_sha = get_commit(base_args, current_sha)
    if not tree_sha:
        return False

    # Create new commit with same tree (empty commit)
    new_commit_sha = create_commit(base_args, message, tree_sha, current_sha)
    if not new_commit_sha:
        return False

    # Update branch reference
    return update_reference(base_args, new_commit_sha)

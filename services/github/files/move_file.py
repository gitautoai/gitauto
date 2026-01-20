# Local imports
from services.github.commits.create_commit import create_commit
from services.github.commits.get_commit import get_commit
from services.github.refs.get_reference import get_reference
from services.github.refs.update_reference import update_reference
from services.github.trees.create_tree import create_tree
from services.github.trees.get_file_tree import get_file_tree
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def move_file(
    old_file_path: str,
    new_file_path: str,
    base_args: BaseArgs,
    **_kwargs,
):
    """Move a file in the GitHub repository using Trees API to ensure Git recognizes it as a rename."""
    if old_file_path == new_file_path:
        return f"Error: old_file_path and new_file_path cannot be the same: {old_file_path}"

    owner = base_args["owner"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]
    skip_ci = base_args.get("skip_ci", False)

    # Get the latest commit SHA
    latest_commit_sha = get_reference(base_args)
    if not latest_commit_sha:
        return f"Error: Could not get reference for branch {new_branch}"

    # Get the tree SHA from the commit
    base_tree_sha = get_commit(base_args, latest_commit_sha)
    if not base_tree_sha:
        return f"Error: Could not get tree SHA for commit {latest_commit_sha}"

    # Get the current tree
    tree_items = get_file_tree(owner, repo, base_tree_sha, token)

    # Find the file to move
    file_blob = None
    for item in tree_items:
        if item["path"] == old_file_path and item["type"] == "blob":
            file_blob = item
            break

    if not file_blob:
        return f"Error: File {old_file_path} not found"

    # Check if new file already exists
    for item in tree_items:
        if item["path"] == new_file_path and item["type"] == "blob":
            return f"Error: Target file {new_file_path} already exists"

    # Create tree items for move operation
    move_tree_items = [
        # Add the file at the new location
        {
            "path": new_file_path,
            "mode": file_blob["mode"],
            "type": "blob",
            "sha": file_blob["sha"],
        },
        # Delete the file from the old location
        {
            "path": old_file_path,
            "mode": file_blob["mode"],
            "type": "blob",
            "sha": None,  # Setting sha to null deletes the file
        },
    ]

    # Create the new tree
    new_tree_sha = create_tree(base_args, base_tree_sha, move_tree_items)
    if not new_tree_sha:
        return "Error: Could not create new tree"

    # Create commit message
    commit_message = (
        f"Move {old_file_path} to {new_file_path} [skip ci]"
        if skip_ci
        else f"Move {old_file_path} to {new_file_path}"
    )

    # Create a new commit
    new_commit_sha = create_commit(
        base_args, commit_message, new_tree_sha, latest_commit_sha
    )
    if not new_commit_sha:
        return "Error: Could not create commit"

    # Update the branch reference
    update_reference(base_args, new_commit_sha)

    return f"File successfully moved from {old_file_path} to {new_file_path}"

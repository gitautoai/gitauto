from services.github.types.github_types import BaseArgs
from services.github.trees.get_file_tree import get_file_tree
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_file_tree_list(base_args: BaseArgs, max_files: int | None = None):
    owner, repo, ref = base_args["owner"], base_args["repo"], base_args["base_branch"]

    # Get complete tree recursively
    tree_items = get_file_tree(owner, repo, ref, base_args["token"])

    # Group files by their depth and collect file info
    paths_by_depth: dict[int, list[str]] = {}
    for item in tree_items:
        if item["type"] != "blob":  # Skip non-file items
            continue
        path = item["path"]
        depth = path.count("/")
        paths_by_depth.setdefault(depth, []).append(path)

    # Collect files starting from shallowest depth
    result: list[str] = []
    max_depth = max(paths_by_depth.keys()) if paths_by_depth else 0

    for depth in range(max_depth + 1):
        if depth in paths_by_depth:
            result.extend(sorted(paths_by_depth[depth]))

    total_files = len(result)
    if max_files and total_files > max_files:
        result = result[:max_files]
        msg = f"Found {total_files} files across {max_depth + 1} directory levels but limited to {max_files} files for now."
    else:
        msg = f"Found {total_files} files across {max_depth + 1} directory levels."

    # Sort the result by alphabetical order
    result.sort()

    return f"{msg}\n\n" + "\n".join(result)

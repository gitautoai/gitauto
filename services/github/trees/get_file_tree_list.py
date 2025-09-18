from services.github.trees.get_file_tree import get_file_tree
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_file_tree_list(base_args: BaseArgs, dir_path: str = "", **_kwargs):
    result: list[str] = []

    # Get the complete tree using existing function
    tree_items = get_file_tree(
        owner=base_args["owner"],
        repo=base_args["repo"],
        ref=base_args["base_branch"],
        token=base_args["token"],
    )

    if not tree_items:
        return result

    files = []
    dirs = []

    # Clean up dir_path (remove leading/trailing whitespace and slashes)
    dir_path = dir_path.strip().strip("/")

    if not dir_path:
        # Show root directory contents (no "/" in path)
        for item in tree_items:
            path = item["path"]
            if "/" not in path:  # Root level only
                if item["type"] == "blob":
                    files.append(path)
                elif item["type"] == "tree":
                    dirs.append(f"{path}/")

        result = sorted(dirs) + sorted(files)
        return result

    # Find items that are direct children of the specified directory
    for item in tree_items:
        path = item["path"]

        # Check if this item is inside our target directory
        if path.startswith(dir_path + "/"):
            # Get the relative path within the directory
            relative_path = path[len(dir_path) + 1 :]

            # Only include direct children (no additional slashes)
            if "/" not in relative_path:
                if item["type"] == "blob":
                    files.append(relative_path)
                elif item["type"] == "tree":
                    dirs.append(f"{relative_path}/")

    if not files and not dirs:
        return result

    result = sorted(dirs) + sorted(files)

    return result

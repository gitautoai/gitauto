import os

from services.git.tree import Tree
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=[], raise_on_error=False)
def get_file_tree(clone_dir: str, ref: str, root_only: bool = False):
    """Lists files in a local git clone using git ls-tree.

    Returns list[Tree] matching the same structure callers expect.
    Requires a local clone with the ref available.
    """
    if not clone_dir or not os.path.isdir(os.path.join(clone_dir, ".git")):
        logger.warning("No valid git repo at %s", clone_dir)
        return []

    # Fetch latest refs to ensure we have the requested ref
    try:
        run_subprocess(args=["git", "fetch", "origin", ref], cwd=clone_dir)
    except ValueError:
        logger.warning("Failed to fetch ref %s, using local data", ref)

    # -r: recursive, -l: show size, --full-tree: show full paths
    args = ["git", "ls-tree", "--full-tree", "-l"]
    if not root_only:
        args.append("-r")
    args.append(f"origin/{ref}")

    try:
        result = run_subprocess(args=args, cwd=clone_dir)
    except ValueError:
        logger.warning("git ls-tree failed for ref %s", ref)
        return []

    output = result.stdout.strip() if result and result.stdout else ""
    if not output:
        return []

    tree_items: list[Tree] = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        # Format: "<mode> <type> <sha> <size>\t<path>"
        # Size is "-" for trees (directories)
        meta, path = line.split("\t", 1)
        parts = meta.split()
        mode = parts[0]
        obj_type = parts[1]
        sha = parts[2]
        size_str = parts[3]

        item: Tree = {
            "path": path,
            "mode": mode,
            "type": obj_type,
            "sha": sha,
        }
        if size_str != "-":
            item["size"] = int(size_str)

        tree_items.append(item)

    return tree_items

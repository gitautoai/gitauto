from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def git_show_head_file(file_path: str, clone_dir: str):
    """Get the last committed version of a file using git show HEAD:<file_path>.
    Returns None if the file doesn't exist in HEAD (new file)."""
    try:
        result = run_subprocess(
            args=["git", "show", f"HEAD:{file_path}"], cwd=clone_dir
        )
    except ValueError:
        # File doesn't exist in HEAD (new file or invalid path)
        return None
    return result.stdout

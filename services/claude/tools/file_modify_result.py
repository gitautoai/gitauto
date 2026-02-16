from dataclasses import dataclass


@dataclass
class FileWriteResult:
    """Result from file write operations (apply_diff, replace_remote_file_content)."""

    success: bool
    message: str
    file_path: str
    content: str
    commit_sha: str = ""


@dataclass
class FileMoveResult:
    """Result from file move operations."""

    success: bool
    message: str
    old_file_path: str
    new_file_path: str

from dataclasses import dataclass


@dataclass
class FileWriteResult:
    """Result from file write operations (apply_diff, write_and_commit_file)."""

    success: bool
    message: str
    file_path: str
    content: str
    diff: str = ""
    commit_sha: str = ""


@dataclass
class FileMoveResult:
    """Result from file move operations."""

    success: bool
    message: str
    old_file_path: str
    new_file_path: str

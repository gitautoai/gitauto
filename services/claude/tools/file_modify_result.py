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
    concurrent_push_detected: bool = False


@dataclass
class FileMoveResult:
    """Result from file move operations."""

    success: bool
    message: str
    old_file_path: str
    new_file_path: str
    concurrent_push_detected: bool = False


@dataclass
class FileDeleteResult:
    """Result from file delete operations."""

    success: bool
    message: str
    file_path: str
    concurrent_push_detected: bool = False

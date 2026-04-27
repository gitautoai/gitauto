import os

from utils.files.list_local_directory import list_local_directory


def test_returns_empty_for_missing_path():
    """Path doesn't exist on disk → empty list (matches the swallow-and-default contract used elsewhere in utils/files; callers don't need to distinguish missing-vs-empty)."""
    assert list_local_directory("/nonexistent/path/at/all") == []


def test_returns_empty_for_path_that_is_a_file(tmp_path):
    """Caller passed a regular file path by mistake → empty list. Mirrors the directory-only contract; callers that care can guard with os.path.isdir themselves."""
    file_path = os.path.join(tmp_path, "file.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("contents")
    assert list_local_directory(file_path) == []


def test_returns_empty_for_empty_directory(tmp_path):
    empty = os.path.join(tmp_path, "empty")
    os.makedirs(empty)
    assert list_local_directory(empty) == []


def test_dirs_first_then_files_each_sorted(tmp_path):
    """The output contract: directories sorted alphabetically with a trailing slash, then files sorted alphabetically. Mirrors `ls -p` ordering."""
    os.makedirs(os.path.join(tmp_path, "zeta"))
    os.makedirs(os.path.join(tmp_path, "alpha"))
    for name in ("foo.py", "bar.py", "ant.py"):
        with open(os.path.join(tmp_path, name), "w", encoding="utf-8") as f:
            f.write("x")

    assert list_local_directory(str(tmp_path)) == [
        "alpha/",
        "zeta/",
        "ant.py",
        "bar.py",
        "foo.py",
    ]


def test_follows_symlinks_to_directories(tmp_path):
    """A symlink that targets a directory shows up as a dir/ entry — os.path.isdir follows symlinks. Symlinks to files show up as plain files."""
    real_dir = os.path.join(tmp_path, "real_dir")
    os.makedirs(real_dir)
    real_file = os.path.join(tmp_path, "real_file.txt")
    with open(real_file, "w", encoding="utf-8") as f:
        f.write("x")
    os.symlink(real_dir, os.path.join(tmp_path, "link_to_dir"))
    os.symlink(real_file, os.path.join(tmp_path, "link_to_file"))

    assert list_local_directory(str(tmp_path)) == [
        "link_to_dir/",
        "real_dir/",
        "link_to_file",
        "real_file.txt",
    ]

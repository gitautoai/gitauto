import os

from utils.files.read_local_file import read_local_file


def test_reads_existing_file(tmp_path):
    file_path = os.path.join(tmp_path, "hello.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("hello world")
    result = read_local_file("hello.txt", base_dir=str(tmp_path))
    assert result == "hello world"


def test_reads_nested_file(tmp_path):
    os.makedirs(os.path.join(tmp_path, "src", "lib"), exist_ok=True)
    file_path = os.path.join(tmp_path, "src", "lib", "utils.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("def foo(): pass")
    result = read_local_file("src/lib/utils.py", base_dir=str(tmp_path))
    assert result == "def foo(): pass"


def test_returns_none_for_missing_file(tmp_path):
    result = read_local_file("nonexistent.py", base_dir=str(tmp_path))
    assert result is None


def test_replaces_malformed_bytes_in_binary_file(tmp_path):
    file_path = os.path.join(tmp_path, "bun.lockb")
    with open(file_path, "wb") as f:
        f.write(b"\x00\x9b\xff\xfe binary content")
    result = read_local_file("bun.lockb", base_dir=str(tmp_path))
    # \x00 stays valid UTF-8 (NUL); \x9b/\xff/\xfe are each replaced by U+FFFD; the trailing space + ASCII bytes survive verbatim.
    assert result == "\x00\ufffd\ufffd\ufffd binary content"


def test_preserves_crlf_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "crlf.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\r\nline2\r\n")
    result = read_local_file("crlf.txt", base_dir=str(tmp_path))
    assert result == "line1\r\nline2\r\n"


def test_preserves_lf_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "lf.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\nline2\n")
    result = read_local_file("lf.txt", base_dir=str(tmp_path))
    assert result == "line1\nline2\n"


def test_preserves_cr_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "cr.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\rline2\r")
    result = read_local_file("cr.txt", base_dir=str(tmp_path))
    assert result == "line1\rline2\r"


def test_returns_none_for_missing_dir():
    result = read_local_file("foo.py", base_dir="/nonexistent/path")
    assert result is None


def test_returns_directory_listing_when_path_is_a_directory(tmp_path):
    """Sentry AGENT-3KP/3KN (Foxquilt/foxcom-payment-frontend PR 566): the agent passed src/auth/__mocks__ (a directory) as a file path. os.path.exists returned True so the old code fell through to open(), which raised IsADirectoryError. New behavior: return the directory listing as a string so the agent can see what's there and pick a real file in a follow-up call, no separate get_local_file_tree round trip."""
    mocks_dir = os.path.join(tmp_path, "src", "auth", "__mocks__")
    os.makedirs(mocks_dir)
    # Mixed contents: two files and a subdirectory.
    with open(os.path.join(mocks_dir, "auth.ts"), "w", encoding="utf-8") as f:
        f.write("export const x = 1;")
    with open(os.path.join(mocks_dir, "user.ts"), "w", encoding="utf-8") as f:
        f.write("export const y = 2;")
    os.makedirs(os.path.join(mocks_dir, "fixtures"))

    result = read_local_file("src/auth/__mocks__", base_dir=str(tmp_path))

    # Directories sorted first with a trailing slash, then files; one entry per line.
    assert result == (
        "# `src/auth/__mocks__` is a directory. Contents:\n"
        "fixtures/\n"
        "auth.ts\n"
        "user.ts"
    )


def test_returns_listing_for_empty_directory(tmp_path):
    """Empty directory still returns the header so the caller knows it was a directory, not a missing path."""
    empty = os.path.join(tmp_path, "empty")
    os.makedirs(empty)

    result = read_local_file("empty", base_dir=str(tmp_path))

    assert result == "# `empty` is a directory. Contents:\n"


def test_returns_none_for_symlink_to_directory_via_non_regular_branch(tmp_path):
    """Symlink to a directory: os.path.isdir follows the link and reports True, so the directory-listing branch fires. The agent gets a listing of whatever the link points at, same as a real directory."""
    real_dir = os.path.join(tmp_path, "real_dir")
    os.makedirs(real_dir)
    with open(os.path.join(real_dir, "thing.txt"), "w", encoding="utf-8") as f:
        f.write("ok")
    link_path = os.path.join(tmp_path, "link_to_dir")
    os.symlink(real_dir, link_path)

    result = read_local_file("link_to_dir", base_dir=str(tmp_path))

    assert result == "# `link_to_dir` is a directory. Contents:\nthing.txt"

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
    assert result is not None
    assert "\ufffd" in result
    assert "binary content" in result


def test_preserves_crlf_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "crlf.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\r\nline2\r\n")
    result = read_local_file("crlf.txt", base_dir=str(tmp_path))
    assert result is not None
    assert "\r\n" in result
    assert result == "line1\r\nline2\r\n"


def test_preserves_lf_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "lf.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\nline2\n")
    result = read_local_file("lf.txt", base_dir=str(tmp_path))
    assert result is not None
    assert "\r\n" not in result
    assert result == "line1\nline2\n"


def test_preserves_cr_line_endings(tmp_path):
    file_path = os.path.join(tmp_path, "cr.txt")
    with open(file_path, "wb") as f:
        f.write(b"line1\rline2\r")
    result = read_local_file("cr.txt", base_dir=str(tmp_path))
    assert result is not None
    assert "\r" in result
    assert "\n" not in result
    assert result == "line1\rline2\r"


def test_returns_none_for_missing_dir():
    result = read_local_file("foo.py", base_dir="/nonexistent/path")
    assert result is None

import os

from utils.files.write_local_file import write_local_file


def test_writes_file(tmp_path):
    result = write_local_file(
        "hello.txt", base_dir=str(tmp_path), content="hello world"
    )
    assert result is True
    with open(os.path.join(tmp_path, "hello.txt"), encoding="utf-8") as f:
        assert f.read() == "hello world"


def test_creates_parent_dirs(tmp_path):
    result = write_local_file(
        "src/lib/utils.py", base_dir=str(tmp_path), content="def foo(): pass"
    )
    assert result is True
    full_path = os.path.join(tmp_path, "src", "lib", "utils.py")
    assert os.path.exists(full_path)
    with open(full_path, encoding="utf-8") as f:
        assert f.read() == "def foo(): pass"


def test_overwrites_existing_file(tmp_path):
    path = os.path.join(tmp_path, "file.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("old content")
    write_local_file("file.txt", base_dir=str(tmp_path), content="new content")
    with open(path, encoding="utf-8") as f:
        assert f.read() == "new content"


def test_writes_empty_content(tmp_path):
    write_local_file("empty.txt", base_dir=str(tmp_path), content="")
    with open(os.path.join(tmp_path, "empty.txt"), encoding="utf-8") as f:
        assert f.read() == ""

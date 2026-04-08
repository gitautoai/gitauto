# pylint: disable=use-implicit-booleaness-not-comparison
import os
import tempfile

from services.git.reapply_files import reapply_files


def test_reapply_files_writes_saved_content():
    with tempfile.TemporaryDirectory() as clone_dir:
        saved_files = {
            "src/app.py": "print('hello')\n",
            "README.md": "# Readme\n",
        }
        result = reapply_files(
            clone_dir=clone_dir, saved_files=saved_files, deleted_files=[]
        )
        assert set(result) == {"src/app.py", "README.md"}
        with open(os.path.join(clone_dir, "src/app.py"), "r", encoding="utf-8") as f:
            assert f.read() == "print('hello')\n"
        with open(os.path.join(clone_dir, "README.md"), "r", encoding="utf-8") as f:
            assert f.read() == "# Readme\n"


def test_reapply_files_deletes_files():
    with tempfile.TemporaryDirectory() as clone_dir:
        target = os.path.join(clone_dir, "old.py")
        with open(target, "w", encoding="utf-8") as f:
            f.write("delete me\n")

        result = reapply_files(
            clone_dir=clone_dir, saved_files={}, deleted_files=["old.py"]
        )
        assert result == ["old.py"]
        assert not os.path.exists(target)


def test_reapply_files_skip_delete_nonexistent():
    with tempfile.TemporaryDirectory() as clone_dir:
        result = reapply_files(
            clone_dir=clone_dir, saved_files={}, deleted_files=["missing.py"]
        )
        assert result == []


def test_reapply_files_creates_subdirectories():
    with tempfile.TemporaryDirectory() as clone_dir:
        saved_files = {"deep/nested/dir/file.py": "content\n"}
        result = reapply_files(
            clone_dir=clone_dir, saved_files=saved_files, deleted_files=[]
        )
        assert result == ["deep/nested/dir/file.py"]
        assert os.path.exists(os.path.join(clone_dir, "deep/nested/dir/file.py"))


def test_reapply_files_empty_input():
    with tempfile.TemporaryDirectory() as clone_dir:
        result = reapply_files(clone_dir=clone_dir, saved_files={}, deleted_files=[])
        assert result == []

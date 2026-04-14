# pyright: reportUnusedVariable=false
from unittest.mock import patch

from services.python.ensure_python_packages import ensure_python_packages

MODULE = "services.python.ensure_python_packages"


def test_returns_false_when_no_manifest():
    with patch(f"{MODULE}.read_local_file", return_value=None):
        result = ensure_python_packages(
            owner_id=123,
            clone_dir="/tmp/owner/repo",
            owner_name="owner",
            repo_name="repo",
        )
        assert result is False


def test_calls_shared_function_with_requirements_txt():
    def read_side_effect(filename, **_kwargs):
        if filename == "requirements.txt":
            return "flask==3.0.0\nrequests==2.31.0"
        if filename == ".python-version":
            return "3.12"
        return None

    with patch(
        f"{MODULE}.detect_python_package_manager",
        return_value=("pip", None, None),
    ):
        with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
            with patch(f"{MODULE}.get_dep_manifest_hash", return_value="abc123"):
                with patch(
                    f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                    return_value=True,
                ) as mock_check:
                    result = ensure_python_packages(
                        owner_id=123,
                        clone_dir="/tmp/clone",
                        owner_name="owner",
                        repo_name="repo",
                    )

                    assert result is True
                    mock_check.assert_called_once_with(
                        owner_name="owner",
                        repo_name="repo",
                        owner_id=123,
                        pkg_manager="pip",
                        tarball_name="venv.tar.gz",
                        manifest_hash="abc123",
                        manifest_files={
                            "requirements.txt": "flask==3.0.0\nrequests==2.31.0",
                            ".python-version": "3.12",
                        },
                        log_prefix="python",
                    )


def test_calls_shared_function_with_pyproject_toml():
    def read_side_effect(filename, **_kwargs):
        if filename == "requirements.txt":
            return None
        if filename == "pyproject.toml":
            return '[project]\nname = "myapp"'
        if filename == ".python-version":
            return None
        return None

    with patch(
        f"{MODULE}.detect_python_package_manager",
        return_value=("pip", None, None),
    ):
        with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
            with patch(f"{MODULE}.get_dep_manifest_hash", return_value="def456"):
                with patch(
                    f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                    return_value=True,
                ) as mock_check:
                    result = ensure_python_packages(
                        owner_id=456,
                        clone_dir="/tmp/clone",
                        owner_name="owner",
                        repo_name="repo",
                    )

                    assert result is True
                    manifest_files = mock_check.call_args.kwargs["manifest_files"]
                    assert "pyproject.toml" in manifest_files
                    assert "requirements.txt" not in manifest_files


def test_includes_poetry_lock_when_detected():
    poetry_lock_content = "[[package]]\nname = flask"

    def read_side_effect(filename, **_kwargs):
        if filename == "requirements.txt":
            return None
        if filename == "pyproject.toml":
            return '[tool.poetry]\nname = "myapp"'
        if filename == ".python-version":
            return None
        return None

    with patch(
        f"{MODULE}.detect_python_package_manager",
        return_value=("poetry", "poetry.lock", poetry_lock_content),
    ):
        with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
            with patch(f"{MODULE}.get_dep_manifest_hash", return_value="ghi789"):
                with patch(
                    f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                    return_value=True,
                ) as mock_check:
                    ensure_python_packages(
                        owner_id=123,
                        clone_dir="/tmp/clone",
                        owner_name="owner",
                        repo_name="repo",
                    )

                    manifest_files = mock_check.call_args.kwargs["manifest_files"]
                    assert "pyproject.toml" in manifest_files
                    assert "poetry.lock" in manifest_files
                    assert mock_check.call_args.kwargs["pkg_manager"] == "poetry"


def test_includes_pipfile_when_pipenv_detected():
    pipfile_lock_content = '{"_meta": {"hash": {"sha256": "abc"}}}'

    def read_side_effect(filename, **_kwargs):
        if filename == "requirements.txt":
            return None
        if filename == "pyproject.toml":
            return None
        if filename == "Pipfile":
            return "[[source]]\nurl = 'https://pypi.org/simple'"
        if filename == ".python-version":
            return None
        return None

    with patch(
        f"{MODULE}.detect_python_package_manager",
        return_value=("pipenv", "Pipfile.lock", pipfile_lock_content),
    ):
        with patch(f"{MODULE}.read_local_file", side_effect=read_side_effect):
            with patch(f"{MODULE}.get_dep_manifest_hash", return_value="jkl012"):
                with patch(
                    f"{MODULE}.check_s3_dep_freshness_and_trigger_install",
                    return_value=True,
                ) as mock_check:
                    ensure_python_packages(
                        owner_id=789,
                        clone_dir="/tmp/clone",
                        owner_name="owner",
                        repo_name="repo",
                    )

                    manifest_files = mock_check.call_args.kwargs["manifest_files"]
                    assert "Pipfile.lock" in manifest_files
                    assert "Pipfile" in manifest_files
                    assert mock_check.call_args.kwargs["pkg_manager"] == "pipenv"

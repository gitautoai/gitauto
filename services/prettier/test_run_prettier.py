import subprocess
from unittest.mock import MagicMock, mock_open, patch

import pytest

from services.prettier.run_prettier import run_prettier


def test_run_prettier_success():
    with patch("services.prettier.run_prettier.os.makedirs"):
        with patch("builtins.open", mock_open()):
            with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                with patch(
                    "builtins.open",
                    mock_open(read_data="const x = 1;\n"),
                ):
                    result = run_prettier(
                        clone_dir="/tmp/test-clone",
                        file_path="src/index.ts",
                        file_content="const x=1",
                    )

                    assert result == "const x = 1;\n"
                    mock_run.assert_called_once()


def test_run_prettier_empty_content():
    result = run_prettier(
        clone_dir="/tmp/test-clone",
        file_path="src/index.ts",
        file_content="",
    )

    assert result is None


def test_run_prettier_whitespace_only():
    result = run_prettier(
        clone_dir="/tmp/test-clone",
        file_path="src/index.ts",
        file_content="   \n\t  ",
    )

    assert result is None


def test_run_prettier_unsupported_file():
    result = run_prettier(
        clone_dir="/tmp/test-clone",
        file_path="src/main.py",
        file_content="def foo(): pass",
    )

    assert result is None


def test_run_prettier_subprocess_failure():
    with patch("services.prettier.run_prettier.os.makedirs"):
        with patch("builtins.open", mock_open()):
            with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stderr="Prettier failed"
                )

                result = run_prettier(
                    clone_dir="/tmp/test-clone",
                    file_path="src/index.ts",
                    file_content="const x=1",
                )

                assert result is None


def test_run_prettier_timeout():
    with patch("services.prettier.run_prettier.os.makedirs"):
        with patch("builtins.open", mock_open()):
            with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="npx prettier", timeout=30
                )

                result = run_prettier(
                    clone_dir="/tmp/test-clone",
                    file_path="src/index.ts",
                    file_content="const x=1",
                )

                assert result is None


@pytest.mark.parametrize(
    "file_path",
    [
        "src/index.js",
        "src/app.jsx",
        "src/main.ts",
        "src/component.tsx",
        "config.json",
        "styles.css",
        "theme.scss",
        "README.md",
        "config.yaml",
        "settings.yml",
    ],
)
def test_run_prettier_supported_extensions(file_path):
    with patch("services.prettier.run_prettier.os.makedirs"):
        with patch("builtins.open", mock_open(read_data="formatted")):
            with patch("services.prettier.run_prettier.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = run_prettier(
                    clone_dir="/tmp/test-clone",
                    file_path=file_path,
                    file_content="content",
                )

                mock_run.assert_called_once()
                assert "npx" in mock_run.call_args[0][0]
                assert "prettier" in mock_run.call_args[0][0]
                assert result == "formatted"

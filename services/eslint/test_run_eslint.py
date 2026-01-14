import json
import subprocess
from unittest.mock import MagicMock, mock_open, patch

import pytest

from services.eslint.run_eslint import run_eslint


def test_run_eslint_skips_non_js_files():
    result = run_eslint(
        clone_dir="/tmp/test-clone",
        file_path="test.py",
        file_content="def foo(): pass",
    )

    assert result is None


def test_run_eslint_skips_empty_content():
    result = run_eslint(
        clone_dir="/tmp/test-clone",
        file_path="test.ts",
        file_content="",
    )

    assert result is None


def test_run_eslint_skips_whitespace_only():
    result = run_eslint(
        clone_dir="/tmp/test-clone",
        file_path="test.ts",
        file_content="   \n\t  ",
    )

    assert result is None


def test_run_eslint_returns_fixed_content():
    fixed_content = "export const foo = 'fixed';\n"
    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open(read_data=fixed_content)):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=eslint_output, stderr=""
                )

                result = run_eslint(
                    clone_dir="/tmp/test-clone",
                    file_path="test.js",
                    file_content="export const foo = 'bar';\n",
                )

    assert result == fixed_content


def test_run_eslint_with_unfixable_errors():
    file_content = "export const foo = 'bar';\n"
    eslint_output = json.dumps(
        [
            {
                "filePath": "test.js",
                "messages": [
                    {
                        "line": 1,
                        "column": 1,
                        "message": "Unexpected var",
                        "ruleId": "no-var",
                        "severity": 2,
                    }
                ],
            }
        ]
    )

    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stdout=eslint_output, stderr=""
                )

                with patch("services.eslint.run_eslint.sentry_sdk.capture_message"):
                    result = run_eslint(
                        clone_dir="/tmp/test-clone",
                        file_path="test.js",
                        file_content=file_content,
                    )

    assert result == file_content


def test_run_eslint_with_json_decode_error():
    file_content = "export const foo = 'bar';\n"

    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout="not json output", stderr=""
                )

                with patch("services.eslint.run_eslint.sentry_sdk.capture_exception"):
                    result = run_eslint(
                        clone_dir="/tmp/test-clone",
                        file_path="test.js",
                        file_content=file_content,
                    )

    assert result == file_content


def test_run_eslint_fatal_error_returns_none():
    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open()):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=2, stdout="", stderr="Fatal error"
                )

                result = run_eslint(
                    clone_dir="/tmp/test-clone",
                    file_path="test.js",
                    file_content="const x = 1;",
                )

    assert result is None


def test_run_eslint_timeout_returns_none():
    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open()):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="npx eslint", timeout=30
                )

                result = run_eslint(
                    clone_dir="/tmp/test-clone",
                    file_path="test.js",
                    file_content="const x = 1;",
                )

    assert result is None


@pytest.mark.parametrize(
    "file_path",
    [
        "src/index.js",
        "src/app.jsx",
        "src/main.ts",
        "src/component.tsx",
    ],
)
def test_run_eslint_supported_extensions(file_path):
    eslint_output = json.dumps([{"filePath": file_path, "messages": []}])

    with patch("services.eslint.run_eslint.os.makedirs"):
        with patch("builtins.open", mock_open(read_data="formatted")):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=eslint_output, stderr=""
                )

                result = run_eslint(
                    clone_dir="/tmp/test-clone",
                    file_path=file_path,
                    file_content="content",
                )

                mock_run.assert_called_once()
                assert "npx" in mock_run.call_args[0][0]
                assert "eslint" in mock_run.call_args[0][0]
                assert result == "formatted"


def test_run_eslint_creates_directories():
    file_content = "const x = 1;"
    eslint_output = json.dumps(
        [{"filePath": "src/deep/nested/test.js", "messages": []}]
    )

    with patch("services.eslint.run_eslint.os.makedirs") as mock_makedirs:
        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("services.eslint.run_eslint.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=eslint_output, stderr=""
                )

                run_eslint(
                    clone_dir="/tmp/test-clone",
                    file_path="src/deep/nested/test.js",
                    file_content=file_content,
                )

                mock_makedirs.assert_called_once()

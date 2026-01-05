import json
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from services.eslint.run_eslint import run_eslint


@pytest.fixture(autouse=True)
def mock_efs_dependencies():
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "services.eslint.run_eslint.is_efs_install_ready", return_value=True
        ):
            with patch("services.eslint.run_eslint.get_efs_dir", return_value=temp_dir):
                yield


SIMPLE_ESLINT_CONFIG = '{"rules": {}}'
SIMPLE_PACKAGE_JSON = '{"devDependencies": {"eslint": "^8.0.0"}}'


def test_run_eslint_skips_non_js_files():
    file_content = """def foo():
    pass
"""

    result = run_eslint(
        owner="test-owner",
        repo="test-repo",
        file_path="test.py",
        file_content=file_content,
        eslint_config_content=SIMPLE_ESLINT_CONFIG,
    )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == file_content


def test_run_eslint_with_empty_content():
    result = run_eslint(
        owner="test-owner",
        repo="test-repo",
        file_path="test.ts",
        file_content="",
        eslint_config_content=SIMPLE_ESLINT_CONFIG,
    )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == ""


def test_run_eslint_skips_without_package_json():
    file_content = """export const foo = 'bar';
"""

    result = run_eslint(
        owner="test-owner",
        repo="test-repo",
        file_path="test.js",
        file_content=file_content,
        eslint_config_content=SIMPLE_ESLINT_CONFIG,
    )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == file_content


def test_run_eslint_returns_fixed_content():
    file_content = """export const foo = 'bar';
"""
    fixed_content = """export const foo = 'fixed';
"""

    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=eslint_output, stderr=""
        )
        mock_run.return_value = mock_result

        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = fixed_content

            result = run_eslint(
                owner="test-owner",
                repo="test-repo",
                file_path="test.js",
                file_content=file_content,
                eslint_config_content=SIMPLE_ESLINT_CONFIG,
                package_json_content=SIMPLE_PACKAGE_JSON,
            )

    assert result is not None
    assert result["success"] is True


def test_run_eslint_with_errors():
    file_content = """export const foo = 'bar';
"""

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

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout=eslint_output, stderr=""
        )
        mock_run.return_value = mock_result

        result = run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=SIMPLE_ESLINT_CONFIG,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

    assert result is not None
    assert result["success"] is False
    assert len(result["errors"]) == 1
    assert result["errors"][0]["message"] == "Unexpected var"


def test_run_eslint_with_json_decode_error():
    file_content = """export const foo = 'bar';
"""

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not json output", stderr=""
        )
        mock_run.return_value = mock_result

        result = run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=SIMPLE_ESLINT_CONFIG,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

        assert result is not None
        assert result["success"] is True
        assert result["fixed_content"] == file_content


def test_run_eslint_with_fatal_error_return_code():
    file_content = """export const foo = 'bar';
"""

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="Fatal error"
        )
        mock_run.return_value = mock_result

        result = run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=SIMPLE_ESLINT_CONFIG,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

        assert result is not None
        assert result["success"] is True  # Decorator returns default on error
        assert result["fixed_content"] == file_content


def test_run_eslint_uses_js_config_for_module_exports():
    file_content = """export const foo = 'bar';
"""
    js_config = """module.exports = { rules: {} };"""

    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=eslint_output, stderr=""
        )
        mock_run.return_value = mock_result

        run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=js_config,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

        call_args = mock_run.call_args[0][0]
        config_path = call_args[call_args.index("--config") + 1]
        assert config_path.endswith(".eslintrc.js")


def test_run_eslint_uses_mjs_config_for_export_default():
    file_content = """export const foo = 'bar';
"""
    mjs_config = """export default { rules: {} };"""

    eslint_output = json.dumps([{"filePath": "test.js", "messages": []}])

    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=eslint_output, stderr=""
        )
        mock_run.return_value = mock_result

        run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=mjs_config,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

        call_args = mock_run.call_args[0][0]
        config_path = call_args[call_args.index("--config") + 1]
        assert config_path.endswith("eslint.config.mjs")


def test_run_eslint_skips_when_efs_install_not_ready():
    file_content = """export const foo = 'bar';
"""

    with patch("services.eslint.run_eslint.is_efs_install_ready", return_value=False):
        result = run_eslint(
            owner="test-owner",
            repo="test-repo",
            file_path="test.js",
            file_content=file_content,
            eslint_config_content=SIMPLE_ESLINT_CONFIG,
            package_json_content=SIMPLE_PACKAGE_JSON,
        )

    assert result is not None
    assert result["success"] is True
    assert result["fixed_content"] == file_content

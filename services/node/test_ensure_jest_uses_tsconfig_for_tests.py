# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import MagicMock, patch

from services.claude.tools.file_modify_result import FileWriteResult
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.types.base_args import BaseArgs


def _mock_success_result(file_path: str = "test.py"):
    """Create a successful FileWriteResult for mocking."""
    return FileWriteResult(
        success=True, message=f"Updated {file_path}", file_path=file_path, content=""
    )


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "test-branch",
            "clone_dir": "/tmp/test",
        },
    )


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_pattern1_ts_jest_string(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Pattern 1: ts-jest as string in transform.

    Before: '^.+\\.tsx?$': 'ts-jest'
    After:  '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.test.json' }]
    """
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
};"""
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_pattern2_ts_jest_array(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Pattern 2: ts-jest as array with options in transform.

    Before: '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true }]
    After:  '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true, tsconfig: 'tsconfig.test.json' }]
    """
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true }],
  },
};"""
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]
    assert "isolatedModules: true" in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_skips_when_already_uses_test_tsconfig(
    mock_get_raw: MagicMock, mock_replace: MagicMock
):
    """Test that we skip if already using the test tsconfig."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.test.json' }],
  },
};"""

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_skips_when_any_tsconfig_configured(
    mock_get_raw: MagicMock, mock_replace: MagicMock
):
    """Test that we skip if any tsconfig is already configured to avoid duplicates."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }],
  },
};"""

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_pattern3_preset_only(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Pattern 3: preset only, no transform block.

    Before: preset: 'ts-jest'
    After:  transform: { '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.test.json' }] }
    """
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
};"""
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]
    assert "transform:" in call_kwargs["file_content"]
    assert "tsx?$" in call_kwargs["file_content"]
    assert "preset" not in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_pattern4_preset_with_existing_transform(
    mock_get_raw: MagicMock, mock_replace: MagicMock
):
    """Pattern 4: preset with existing transform block.

    Before: preset: 'ts-jest', transform: { '^.+\\.handlebars$': 'handlebars-jest' }
    After:  transform: { '^.+\\.tsx?$': ['ts-jest', { tsconfig: '...' }], '^.+\\.handlebars$': 'handlebars-jest' }
    """
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  preset: 'ts-jest',
  transform: {
    '^.+\\.handlebars$': 'handlebars-jest',
  },
};"""
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]
    assert "tsx?$" in call_kwargs["file_content"]
    assert "handlebars-jest" in call_kwargs["file_content"]
    assert "preset" not in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_returns_none_when_no_pattern(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test that None is returned when no ts-jest pattern found."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  testEnvironment: 'node',
};"""

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_handles_double_quotes(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test handling double quotes in Jest config."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    "^.+\\.tsx?$": "ts-jest",
  },
};"""
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.write_and_commit_file")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.read_local_file")
def test_skips_when_no_jest_config(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test that None is returned when no Jest config exists."""
    root_files = ["tsconfig.json", "package.json"]

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()

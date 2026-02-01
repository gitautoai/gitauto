# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
from typing import cast
from unittest.mock import MagicMock, patch

from services.github.types.github_types import BaseArgs
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)


def _make_base_args():
    return cast(
        BaseArgs,
        {
            "owner": "test-owner",
            "repo": "test-repo",
            "token": "test-token",
            "new_branch": "test-branch",
        },
    )


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
def test_converts_string_to_array(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test converting ts-jest string config to array with tsconfig."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
  },
};"""
    mock_replace.return_value = "Success"

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
def test_adds_to_existing_array(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test adding tsconfig to existing ts-jest array config."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { isolatedModules: true }],
  },
};"""
    mock_replace.return_value = "Success"

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert "tsconfig.test.json" in call_kwargs["file_content"]
    assert "isolatedModules: true" in call_kwargs["file_content"]


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
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


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
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


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
def test_returns_none_when_no_pattern(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test that None is returned when no ts-jest pattern found."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  preset: 'ts-jest',
};"""

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
def test_handles_double_quotes(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test handling double quotes in Jest config."""
    root_files = ["jest.config.js", "tsconfig.json"]
    mock_get_raw.return_value = """module.exports = {
  transform: {
    "^.+\\.tsx?$": "ts-jest",
  },
};"""
    mock_replace.return_value = "Success"

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path == "jest.config.js"
    assert status == "modified"


@patch("services.node.ensure_jest_uses_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_jest_uses_tsconfig_for_tests.get_raw_content")
def test_skips_when_no_jest_config(mock_get_raw: MagicMock, mock_replace: MagicMock):
    """Test that None is returned when no Jest config exists."""
    root_files = ["tsconfig.json", "package.json"]

    path, status = ensure_jest_uses_tsconfig_for_tests(
        root_files, _make_base_args(), "tsconfig.test.json"
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()

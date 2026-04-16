# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from unittest.mock import MagicMock, patch

import jsonc

from services.claude.tools.file_modify_result import FileWriteResult
from services.node.ensure_tsconfig_relaxed_for_tests import (
    ensure_tsconfig_relaxed_for_tests,
)


def _mock_success_result(file_path: str = "test.py"):
    """Create a successful FileWriteResult for mocking."""
    return FileWriteResult(
        success=True, message=f"Updated {file_path}", file_path=file_path, content=""
    )


def test_jsonc_strips_single_line_comments():
    content = '{\n  "foo": "bar" // comment\n}'
    result = jsonc.loads(content)
    assert result == {"foo": "bar"}


def test_jsonc_strips_multi_line_comments():
    content = '{\n  /* comment */\n  "foo": "bar"\n}'
    result = jsonc.loads(content)
    assert result == {"foo": "bar"}


def test_jsonc_strips_trailing_commas():
    content = '{\n  "foo": "bar",\n}'
    result = jsonc.loads(content)
    assert result == {"foo": "bar"}


def test_jsonc_handles_complex_tsconfig():
    content = """{
  // This is a comment
  "compilerOptions": {
    "strict": true, /* inline comment */
    "noUnusedLocals": false,
  },
}"""
    result = jsonc.loads(content)
    assert result["compilerOptions"]["strict"] is True
    assert result["compilerOptions"]["noUnusedLocals"] is False


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_creates_file_when_no_variants_exist(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json"]
    mock_get_raw.return_value = None
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.test.json"
    assert status == "added"
    mock_replace.assert_called_once()


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_skips_when_variant_has_correct_settings(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "tsconfig.spec.json"]
    mock_get_raw.return_value = json.dumps(
        {"compilerOptions": {"noUnusedLocals": False, "noUnusedParameters": False}}
    )

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.spec.json"
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_updates_variant_when_missing_settings(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "tsconfig.build.json"]

    def read_side_effect(file_path, base_dir):
        if file_path == "tsconfig.build.json":
            return '{"compilerOptions": {"noUnusedLocals": true}}'
        return None

    mock_get_raw.side_effect = read_side_effect
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.build.json"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert call_kwargs["file_path"] == "tsconfig.build.json"
    assert '"noUnusedLocals": false' in call_kwargs["file_content"]
    assert '"noUnusedParameters": false' in call_kwargs["file_content"]


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_updates_existing_tsconfig_test(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "tsconfig.test.json"]

    existing_config = """{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true
  }
}"""

    def read_side_effect(file_path, base_dir):
        if file_path == "tsconfig.test.json":
            return existing_config
        return None

    mock_get_raw.side_effect = read_side_effect
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.test.json"
    assert status == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    updated_content = json.loads(call_kwargs["file_content"])
    assert updated_content["compilerOptions"]["noUnusedLocals"] is False
    assert updated_content["compilerOptions"]["noUnusedParameters"] is False
    assert updated_content["compilerOptions"]["strict"] is True


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_ignores_nested_tsconfig_files(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "packages/foo/tsconfig.test.json"]
    mock_get_raw.return_value = None
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.test.json"
    assert status == "added"


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_creates_when_only_main_tsconfig_exists(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json"]
    mock_get_raw.return_value = None
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.test.json"
    assert status == "added"


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_skips_non_typescript_repo(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["package.json", "index.js"]
    mock_get_raw.return_value = None
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_skips_when_variant_has_invalid_json(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "tsconfig.spec.json"]

    def read_side_effect(file_path, base_dir):
        if file_path == "tsconfig.spec.json":
            return "invalid json {"
        return None

    mock_get_raw.side_effect = read_side_effect
    mock_replace.return_value = _mock_success_result()

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path is None
    assert status is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_tsconfig_relaxed_for_tests.write_and_commit_file")
@patch("services.node.ensure_tsconfig_relaxed_for_tests.read_local_file")
def test_handles_tsconfig_with_comments(
    mock_get_raw: MagicMock, mock_replace: MagicMock, create_test_base_args
):
    root_files = ["tsconfig.json", "tsconfig.spec.json"]

    tsconfig_with_comments = """{
  // TypeScript config for tests
  "compilerOptions": {
    "noUnusedLocals": false, /* allow unused */
    "noUnusedParameters": false,
  }
}"""

    mock_get_raw.return_value = tsconfig_with_comments

    path, status = ensure_tsconfig_relaxed_for_tests(
        root_files, create_test_base_args()
    )

    assert path == "tsconfig.spec.json"
    assert status is None
    mock_replace.assert_not_called()

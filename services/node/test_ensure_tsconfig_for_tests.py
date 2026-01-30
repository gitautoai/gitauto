# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from typing import cast
from unittest.mock import MagicMock, patch

from services.github.types.github_types import BaseArgs
from services.node.ensure_tsconfig_for_tests import ensure_tsconfig_for_tests


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


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_creates_file_when_no_variants_exist(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [{"type": "blob", "path": "tsconfig.json"}]
    mock_get_raw.return_value = None
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result == "Created tsconfig.test.json"
    mock_replace.assert_called_once()


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_skips_when_variant_has_correct_settings(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "tsconfig.json"},
        {"type": "blob", "path": "tsconfig.spec.json"},
    ]
    mock_get_raw.return_value = json.dumps(
        {"compilerOptions": {"noUnusedLocals": False, "noUnusedParameters": False}}
    )

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_creates_when_variant_has_wrong_settings(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "tsconfig.json"},
        {"type": "blob", "path": "tsconfig.spec.json"},
    ]

    def get_raw_side_effect(owner, repo, file_path, ref, token):
        if file_path == "tsconfig.spec.json":
            return json.dumps({"compilerOptions": {"noUnusedLocals": True}})
        return None

    mock_get_raw.side_effect = get_raw_side_effect
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Update tsconfig for relaxed test file checking",
    )

    assert result == "Updated tsconfig.spec.json"


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_updates_existing_tsconfig_test(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "tsconfig.json"},
        {"type": "blob", "path": "tsconfig.test.json"},
    ]

    def get_raw_side_effect(owner, repo, file_path, ref, token):
        if file_path == "tsconfig.test.json":
            return json.dumps(
                {"extends": "./tsconfig.json", "compilerOptions": {"strict": True}}
            )
        return None

    mock_get_raw.side_effect = get_raw_side_effect
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Update tsconfig.test.json with relaxed settings for tests",
    )

    assert result == "Updated tsconfig.test.json"
    call_kwargs = mock_replace.call_args.kwargs
    content = json.loads(call_kwargs["file_content"])
    assert content["compilerOptions"]["noUnusedLocals"] is False
    assert content["compilerOptions"]["noUnusedParameters"] is False
    assert content["compilerOptions"]["strict"] is True


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_ignores_nested_tsconfig_files(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "tsconfig.json"},
        {"type": "blob", "path": "packages/foo/tsconfig.test.json"},
    ]
    mock_get_raw.return_value = None
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result == "Created tsconfig.test.json"


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_creates_when_only_main_tsconfig_exists(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [{"type": "blob", "path": "tsconfig.json"}]
    mock_get_raw.return_value = None
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result == "Created tsconfig.test.json"


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_skips_non_typescript_repo(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "package.json"},
        {"type": "blob", "path": "index.js"},
    ]
    mock_get_raw.return_value = None
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result is None
    mock_replace.assert_not_called()


@patch("services.node.ensure_tsconfig_for_tests.replace_remote_file_content")
@patch("services.node.ensure_tsconfig_for_tests.get_raw_content")
@patch("services.node.ensure_tsconfig_for_tests.get_file_tree")
def test_handles_invalid_json_in_variant(
    mock_tree: MagicMock, mock_get_raw: MagicMock, mock_replace: MagicMock
):
    mock_tree.return_value = [
        {"type": "blob", "path": "tsconfig.json"},
        {"type": "blob", "path": "tsconfig.spec.json"},
    ]

    def get_raw_side_effect(owner, repo, file_path, ref, token):
        if file_path == "tsconfig.spec.json":
            return "invalid json {"
        return None

    mock_get_raw.side_effect = get_raw_side_effect
    mock_replace.return_value = "Success"

    result = ensure_tsconfig_for_tests(
        base_args=_make_base_args(),
        commit_message="Add tsconfig.test.json for relaxed test file checking",
    )

    assert result is None
    mock_replace.assert_not_called()

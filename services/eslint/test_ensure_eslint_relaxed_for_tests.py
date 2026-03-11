# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false
import json
from typing import cast
from unittest.mock import MagicMock, patch

from services.claude.tools.file_modify_result import FileWriteResult
from services.eslint.ensure_eslint_relaxed_for_tests import (
    RELAXED_RULES,
    TEST_FILE_GLOBS,
    ensure_eslint_relaxed_for_tests,
)
from services.types.base_args import BaseArgs


def _mock_success_result(file_path: str = ".eslintrc.json"):
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
            "base_branch": "main",
            "clone_dir": "/tmp/test-clone",
        },
    )


def test_returns_none_when_empty_content():
    config = {"filename": ".eslintrc.json", "content": ""}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_returns_none_when_empty_filename():
    config = {"filename": "", "content": "{}"}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_skips_js_config():
    config = {"filename": ".eslintrc.js", "content": "module.exports = {}"}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_skips_yaml_config():
    config = {"filename": ".eslintrc.yaml", "content": "rules: {}"}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_skips_flat_config():
    config = {"filename": "eslint.config.js", "content": "export default {}"}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_returns_none_when_invalid_json():
    config = {"filename": ".eslintrc.json", "content": "invalid json {"}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_skips_when_override_already_exists():
    existing_config = {
        "rules": {},
        "overrides": [
            {
                "files": ["**/*.test.*"],
                "rules": {"@typescript-eslint/no-explicit-any": "off"},
            }
        ],
    }
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


def test_skips_when_override_exists_with_numeric_off():
    existing_config = {
        "rules": {},
        "overrides": [
            {
                "files": ["**/*.spec.*"],
                "rules": {"@typescript-eslint/no-explicit-any": 0},
            }
        ],
    }
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )
    assert result is None


@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_adds_override_to_eslintrc_json(mock_replace: MagicMock):
    existing_config = {"rules": {"semi": "error"}}
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    mock_replace.return_value = _mock_success_result()

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result == "modified"
    mock_replace.assert_called_once()
    call_kwargs = mock_replace.call_args.kwargs
    assert call_kwargs["file_path"] == ".eslintrc.json"
    updated = json.loads(call_kwargs["file_content"])
    assert len(updated["overrides"]) == 1
    assert updated["overrides"][0]["files"] == TEST_FILE_GLOBS
    assert updated["overrides"][0]["rules"] == RELAXED_RULES


@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_adds_override_to_eslintrc(mock_replace: MagicMock):
    existing_config = {"extends": "eslint:recommended"}
    config = {"filename": ".eslintrc", "content": json.dumps(existing_config)}
    mock_replace.return_value = _mock_success_result(".eslintrc")

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert call_kwargs["file_path"] == ".eslintrc"


@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_appends_to_existing_overrides(mock_replace: MagicMock):
    existing_config = {
        "rules": {},
        "overrides": [
            {"files": ["*.js"], "rules": {"no-console": "off"}},
        ],
    }
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    mock_replace.return_value = _mock_success_result()

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    updated = json.loads(call_kwargs["file_content"])
    assert len(updated["overrides"]) == 2
    assert updated["overrides"][0]["files"] == ["*.js"]
    assert updated["overrides"][1]["files"] == TEST_FILE_GLOBS


@patch("services.eslint.ensure_eslint_relaxed_for_tests.read_local_file")
@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_wraps_in_package_json(mock_replace: MagicMock, mock_read: MagicMock):
    eslint_config_content = {"rules": {"semi": "error"}}
    config = {"filename": "package.json", "content": json.dumps(eslint_config_content)}

    full_package = {
        "name": "my-app",
        "version": "1.0.0",
        "eslintConfig": eslint_config_content,
    }
    mock_read.return_value = json.dumps(full_package)
    mock_replace.return_value = _mock_success_result("package.json")

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert call_kwargs["file_path"] == "package.json"
    updated = json.loads(call_kwargs["file_content"])
    assert "name" in updated
    assert "eslintConfig" in updated
    assert len(updated["eslintConfig"]["overrides"]) == 1
    assert updated["eslintConfig"]["overrides"][0]["rules"] == RELAXED_RULES


@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_returns_none_when_replace_fails(mock_replace: MagicMock):
    existing_config = {"rules": {}}
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    mock_replace.return_value = FileWriteResult(
        success=False, message="API error", file_path=".eslintrc.json", content=""
    )

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result is None


@patch("services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content")
def test_real_foxquilt_eslintrc(mock_replace: MagicMock):
    """Test with real Foxquilt foxcom-payment-frontend .eslintrc that caused the original bug.
    It extends @typescript-eslint/recommended (which enables no-explicit-any as warn)
    and has no existing overrides for test files."""
    with open(
        "payloads/eslint/foxquilt_foxcom_payment_frontend.json", "r", encoding="utf-8"
    ) as f:
        real_config = json.load(f)
    config = {"filename": ".eslintrc", "content": json.dumps(real_config)}
    mock_replace.return_value = _mock_success_result(".eslintrc")

    result = ensure_eslint_relaxed_for_tests(
        eslint_config=config, base_args=_make_base_args()
    )

    assert result == "modified"
    call_kwargs = mock_replace.call_args.kwargs
    assert call_kwargs["file_path"] == ".eslintrc"
    updated = json.loads(call_kwargs["file_content"])
    # Original config should be preserved
    assert updated["parser"] == "@typescript-eslint/parser"
    assert "plugin:@typescript-eslint/recommended" in updated["extends"]
    assert updated["rules"]["@typescript-eslint/no-unused-vars"] == "error"
    # Override should be added
    assert len(updated["overrides"]) == 1
    assert updated["overrides"][0]["files"] == TEST_FILE_GLOBS
    assert updated["overrides"][0]["rules"] == RELAXED_RULES


def test_does_not_match_override_without_test_glob():
    existing_config = {
        "overrides": [
            {
                "files": ["*.js"],
                "rules": {"@typescript-eslint/no-explicit-any": "off"},
            }
        ],
    }
    config = {"filename": ".eslintrc.json", "content": json.dumps(existing_config)}
    # Should NOT skip - the override is for *.js, not test files
    # But it will try to modify, which needs a mock for replace_remote_file_content
    with patch(
        "services.eslint.ensure_eslint_relaxed_for_tests.replace_remote_file_content"
    ) as mock_replace:
        mock_replace.return_value = _mock_success_result()
        result = ensure_eslint_relaxed_for_tests(
            eslint_config=config, base_args=_make_base_args()
        )
        assert result == "modified"

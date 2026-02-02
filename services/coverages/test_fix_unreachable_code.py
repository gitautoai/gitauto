# pylint: disable=redefined-outer-name,unused-argument
# pyright: reportArgumentType=false,reportUnusedVariable=false
from unittest.mock import MagicMock, patch

import pytest

from services.coverages.fix_unreachable_code import fix_unreachable_code


class MockTask:
    def __await__(self):
        return iter([])


@pytest.fixture
def mock_clone_task():
    return MockTask()


@pytest.mark.asyncio
async def test_skips_non_js_ts_files(mock_clone_task):
    result = await fix_unreachable_code(
        file_path="file.py",
        repo_dir="/repo",
        clone_task=mock_clone_task,
        root_files=["tsconfig.json"],
        base_args={},
    )
    assert result.fixed_content is None
    assert not result.unfixable_lines


@pytest.mark.asyncio
async def test_skips_if_no_tsconfig(mock_clone_task, tmp_path):
    ts_file = tmp_path / "test.ts"
    ts_file.write_text("const x = 1;")

    result = await fix_unreachable_code(
        file_path="test.ts",
        repo_dir=str(tmp_path),
        clone_task=mock_clone_task,
        root_files=[],
        base_args={},
    )

    assert result.fixed_content is None
    assert not result.unfixable_lines


@pytest.mark.asyncio
async def test_skips_if_typescript_eslint_missing(mock_clone_task, tmp_path):
    ts_file = tmp_path / "test.ts"
    ts_file.write_text("const x = 1;")

    with patch("os.path.exists", return_value=False):
        result = await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    assert result.fixed_content is None
    assert not result.unfixable_lines


@pytest.mark.asyncio
async def test_eslint_fix_changes_file(mock_clone_task, tmp_path):
    (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
    (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
    (tmp_path / "node_modules/typescript").mkdir(parents=True)

    ts_file = tmp_path / "test.ts"
    original_content = "const x: string = 'hello'; const len = x?.length;"
    fixed_content = "const x: string = 'hello'; const len = x.length;"
    ts_file.write_text(original_content)

    def mock_run(*args, **kwargs):
        ts_file.write_text(fixed_content)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_result.stderr = ""
        return mock_result

    with patch("subprocess.run", side_effect=mock_run):
        result = await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    assert result.fixed_content == fixed_content
    assert not result.unfixable_lines


@pytest.mark.asyncio
async def test_eslint_returns_unfixable_issues(mock_clone_task, tmp_path):
    (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
    (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
    (tmp_path / "node_modules/typescript").mkdir(parents=True)

    ts_file = tmp_path / "test.ts"
    content = "const x: string = 'hello'; if (x === null) { console.log('dead'); }"
    ts_file.write_text(content)

    eslint_output = """[{
        "messages": [
            {
                "ruleId": "@typescript-eslint/no-unnecessary-condition",
                "line": 1,
                "message": "Unnecessary conditional, the types have no overlap"
            }
        ]
    }]"""

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = eslint_output
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        result = await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    assert result.fixed_content is None
    assert result.unfixable_lines == {
        1: "Unnecessary conditional, the types have no overlap"
    }


@pytest.mark.asyncio
async def test_eslint_fixes_and_reports_remaining(mock_clone_task, tmp_path):
    (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
    (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
    (tmp_path / "node_modules/typescript").mkdir(parents=True)

    ts_file = tmp_path / "test.ts"
    original = "const x: string = 'a'; const len = x?.length; if (x === null) {}"
    fixed = "const x: string = 'a'; const len = x.length; if (x === null) {}"
    ts_file.write_text(original)

    eslint_output = """[{
        "messages": [
            {
                "ruleId": "@typescript-eslint/no-unnecessary-condition",
                "line": 1,
                "message": "Unnecessary conditional, the types have no overlap"
            }
        ]
    }]"""

    def mock_run(*args, **kwargs):
        ts_file.write_text(fixed)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = eslint_output
        mock_result.stderr = ""
        return mock_result

    with patch("subprocess.run", side_effect=mock_run):
        result = await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    assert result.fixed_content == fixed
    assert result.unfixable_lines == {
        1: "Unnecessary conditional, the types have no overlap"
    }


@pytest.mark.asyncio
async def test_eslint_no_stdout_but_stderr(mock_clone_task, tmp_path):
    (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
    (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
    (tmp_path / "node_modules/typescript").mkdir(parents=True)

    ts_file = tmp_path / "test.ts"
    ts_file.write_text("const x = 1;")

    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = ""
    mock_result.stderr = "Error: tsconfig.json not found"

    with patch("subprocess.run", return_value=mock_result):
        result = await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    assert result.fixed_content is None
    assert not result.unfixable_lines


@pytest.mark.asyncio
async def test_uses_legacy_config_mode(mock_clone_task, tmp_path):
    (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
    (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
    (tmp_path / "node_modules/typescript").mkdir(parents=True)

    ts_file = tmp_path / "test.ts"
    ts_file.write_text("const x = 1;")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "[]"
    mock_result.stderr = ""

    with (
        patch(
            "services.coverages.fix_unreachable_code.get_eslint_config"
        ) as mock_eslint_config,
        patch("subprocess.run", return_value=mock_result) as mock_run,
    ):
        mock_eslint_config.return_value = {
            "filename": ".eslintrc.json",
            "content": "{}",
        }
        await fix_unreachable_code(
            file_path="test.ts",
            repo_dir=str(tmp_path),
            clone_task=mock_clone_task,
            root_files=["tsconfig.json"],
            base_args={},
        )

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["env"]["ESLINT_USE_FLAT_CONFIG"] == "false"

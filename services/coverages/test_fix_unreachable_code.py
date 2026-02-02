# pylint: disable=redefined-outer-name,unused-argument
from unittest.mock import MagicMock, patch

import pytest

from services.coverages.fix_unreachable_code import (
    UnreachableCodeResult,
    fix_unreachable_code,
)


class MockTask:
    """A mock asyncio.Task that can be awaited."""

    def __await__(self):
        return iter([])


@pytest.fixture
def mock_clone_task():
    return MockTask()


class TestUnreachableCodeResult:
    def test_default_values(self):
        result = UnreachableCodeResult()
        assert result.fixed_content is None
        assert not result.unfixable_lines

    def test_with_values(self):
        result = UnreachableCodeResult(
            fixed_content="const x = 1;",
            unfixable_lines={10: "Unnecessary condition"},
        )
        assert result.fixed_content == "const x = 1;"
        assert result.unfixable_lines == {10: "Unnecessary condition"}


class TestFixUnreachableCode:
    @pytest.mark.asyncio
    async def test_skips_non_js_ts_files(self, mock_clone_task):
        result = await fix_unreachable_code("file.py", "/repo", mock_clone_task)
        assert result.fixed_content is None
        assert not result.unfixable_lines

    @pytest.mark.asyncio
    async def test_skips_if_typescript_eslint_missing(self, mock_clone_task, tmp_path):
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x = 1;")

        with patch("os.path.exists", return_value=False):
            result = await fix_unreachable_code(
                "test.ts", str(tmp_path), mock_clone_task
            )

        assert result.fixed_content is None
        assert not result.unfixable_lines

    @pytest.mark.asyncio
    async def test_eslint_fix_changes_file(self, mock_clone_task, tmp_path):
        # Setup required paths
        (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
        (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
        (tmp_path / "node_modules/typescript").mkdir(parents=True)
        (tmp_path / "tsconfig.json").write_text("{}")

        ts_file = tmp_path / "test.ts"
        original_content = "const x: string = 'hello'; const len = x?.length;"
        fixed_content = "const x: string = 'hello'; const len = x.length;"
        ts_file.write_text(original_content)

        eslint_output = "[]"  # No remaining errors

        def mock_run(*args, **kwargs):
            # Simulate ESLint --fix modifying the file
            ts_file.write_text(fixed_content)
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = eslint_output
            mock_result.stderr = ""
            return mock_result

        with patch("subprocess.run", side_effect=mock_run):
            result = await fix_unreachable_code(
                "test.ts", str(tmp_path), mock_clone_task
            )

        assert result.fixed_content == fixed_content
        assert not result.unfixable_lines

    @pytest.mark.asyncio
    async def test_eslint_returns_unfixable_issues(self, mock_clone_task, tmp_path):
        # Setup required paths
        (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
        (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
        (tmp_path / "node_modules/typescript").mkdir(parents=True)
        (tmp_path / "tsconfig.json").write_text("{}")

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
                "test.ts", str(tmp_path), mock_clone_task
            )

        # File unchanged, so fixed_content is None
        assert result.fixed_content is None
        assert result.unfixable_lines == {
            1: "Unnecessary conditional, the types have no overlap"
        }

    @pytest.mark.asyncio
    async def test_eslint_fixes_and_reports_remaining(self, mock_clone_task, tmp_path):
        # Setup required paths
        (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
        (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
        (tmp_path / "node_modules/typescript").mkdir(parents=True)
        (tmp_path / "tsconfig.json").write_text("{}")

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
            # Simulate ESLint --fix modifying the file
            ts_file.write_text(fixed)
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = eslint_output
            mock_result.stderr = ""
            return mock_result

        with patch("subprocess.run", side_effect=mock_run):
            result = await fix_unreachable_code(
                "test.ts", str(tmp_path), mock_clone_task
            )

        # ESLint fixed the optional chain but couldn't fix the condition
        assert result.fixed_content == fixed
        assert result.unfixable_lines == {
            1: "Unnecessary conditional, the types have no overlap"
        }

    @pytest.mark.asyncio
    async def test_eslint_no_stdout_but_stderr(self, mock_clone_task, tmp_path):
        # Setup required paths
        (tmp_path / "node_modules/@typescript-eslint/eslint-plugin").mkdir(parents=True)
        (tmp_path / "node_modules/@typescript-eslint/parser").mkdir(parents=True)
        (tmp_path / "node_modules/typescript").mkdir(parents=True)
        (tmp_path / "tsconfig.json").write_text("{}")

        ts_file = tmp_path / "test.ts"
        content = "const x = 1;"
        ts_file.write_text(content)

        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_result.stderr = "Error: tsconfig.json not found"

        with patch("subprocess.run", return_value=mock_result):
            result = await fix_unreachable_code(
                "test.ts", str(tmp_path), mock_clone_task
            )

        # No changes, no unfixable issues (just an error)
        assert result.fixed_content is None
        assert not result.unfixable_lines

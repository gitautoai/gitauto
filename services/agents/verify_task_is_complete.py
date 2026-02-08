from dataclasses import dataclass, field

from constants.files import JS_TEST_FILE_EXTENSIONS, TS_TEST_FILE_EXTENSIONS
from services.eslint.run_eslint_fix import run_eslint_fix
from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.trees.get_file_tree import get_file_tree
from services.github.types.github_types import BaseArgs
from services.jest.run_jest_test import run_jest_test
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.node.ensure_tsconfig_for_tests import ensure_tsconfig_for_tests
from services.prettier.run_prettier_fix import run_prettier_fix
from services.tsc.create_tsc_issue import create_tsc_issue
from services.tsc.run_tsc_check import run_tsc_check
from utils.error.handle_exceptions import handle_exceptions
from utils.files.filter_js_ts_files import filter_js_ts_files
from utils.logging.logging_config import logger


@dataclass
class VerifyTaskIsCompleteResult:
    success: bool
    message: str
    fixes_applied: list[str] = field(default_factory=list)


@handle_exceptions(
    default_return_value=VerifyTaskIsCompleteResult(
        success=False,
        message="Verification failed due to an unexpected error.",
    ),
    raise_on_error=False,
)
async def verify_task_is_complete(base_args: BaseArgs, **_kwargs):
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    pull_number = base_args.get("pull_number")
    token = base_args.get("token", "")
    new_branch = base_args.get("new_branch", "")

    if not pull_number:
        raise ValueError("pull_number is required for verify_task_is_complete")

    pr_files = get_pull_request_files(
        owner=owner, repo=repo, pull_number=pull_number, token=token
    )

    if not pr_files:
        return VerifyTaskIsCompleteResult(
            success=False,
            message="Error: Cannot complete task - the PR has no changes. You must make actual code changes before calling verify_task_is_complete. Use apply_diff_to_file or replace_remote_file_content to commit your changes first.",
        )

    js_test_files = [
        f["filename"]
        for f in pr_files
        if f["filename"].endswith(JS_TEST_FILE_EXTENSIONS) and f["status"] != "removed"
    ]

    ts_test_files = [f for f in js_test_files if f.endswith(TS_TEST_FILE_EXTENSIONS)]
    if ts_test_files:
        tree_items = get_file_tree(
            owner=owner, repo=repo, ref=new_branch, token=token, root_only=True
        )
        root_files = [item["path"] for item in tree_items if item["type"] == "blob"]

        tsconfig_path, _ = ensure_tsconfig_for_tests(
            root_files=root_files,
            base_args=base_args,
        )
        if tsconfig_path:
            ensure_jest_uses_tsconfig_for_tests(
                root_files=root_files,
                base_args=base_args,
                tsconfig_path=tsconfig_path,
            )

    non_removed_files = [f["filename"] for f in pr_files if f["status"] != "removed"]
    js_ts_files = filter_js_ts_files(non_removed_files)

    formatting_applied: list[str] = []
    remaining_errors: list[str] = []
    for file_path in js_ts_files:
        content = get_raw_content(
            owner=owner, repo=repo, file_path=file_path, ref=new_branch, token=token
        )
        if not content:
            continue

        prettier_result = await run_prettier_fix(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if prettier_result.content and prettier_result.content != content:
            replace_remote_file_content(
                file_content=prettier_result.content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Format {file_path} with Prettier",
            )
            content = prettier_result.content
            formatting_applied.append(f"- {file_path}: Prettier")
        if prettier_result.error:
            remaining_errors.append(f"- {file_path}: Prettier: {prettier_result.error}")

        eslint_result = await run_eslint_fix(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if eslint_result.content and eslint_result.content != content:
            replace_remote_file_content(
                file_content=eslint_result.content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Lint {file_path} with ESLint",
            )
            formatting_applied.append(f"- {file_path}: ESLint")
        eslint_all = [
            e for e in [eslint_result.lint_errors, eslint_result.coverage_errors] if e
        ]
        if eslint_all:
            remaining_errors.append(f"- {file_path}: ESLint: {'; '.join(eslint_all)}")

    if formatting_applied:
        logger.info("Applied formatting to files:\n%s", "\n".join(formatting_applied))

    # Run tsc type check on all non-removed files
    tsc_result = await run_tsc_check(base_args=base_args, file_paths=non_removed_files)
    if tsc_result.errors:
        baseline = base_args.get("baseline_tsc_errors", set())
        unrelated_tsc_errors: list[str] = []
        for err in tsc_result.errors:
            if err in baseline:
                unrelated_tsc_errors.append(err)
            else:
                remaining_errors.append(f"- tsc: {err}")
        if unrelated_tsc_errors:
            logger.info(
                "tsc: %d pre-existing errors skipped", len(unrelated_tsc_errors)
            )
            create_tsc_issue(base_args=base_args, unrelated_errors=unrelated_tsc_errors)

    # Run jest/vitest tests on test files
    jest_result = await run_jest_test(base_args=base_args, file_paths=non_removed_files)
    if jest_result.errors:
        for err in jest_result.errors:
            remaining_errors.append(f"- {jest_result.runner_name}: {err}")

    if remaining_errors:
        error_msg = "\n".join(remaining_errors)
        logger.warning("Remaining errors after fixes:\n%s", error_msg)
        return VerifyTaskIsCompleteResult(
            success=False,
            message=f"Task NOT complete. Fix these errors:\n{error_msg}",
            fixes_applied=formatting_applied,
        )

    return VerifyTaskIsCompleteResult(
        success=True,
        message="Task completed.",
        fixes_applied=formatting_applied,
    )

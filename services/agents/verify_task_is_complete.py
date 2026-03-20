import os
from dataclasses import dataclass, field

from constants.files import (
    JS_TEST_FILE_EXTENSIONS,
    PHP_TEST_FILE_EXTENSIONS,
    TS_TEST_FILE_EXTENSIONS,
)
from services.eslint.ensure_eslint_relaxed_for_tests import (
    ensure_eslint_relaxed_for_tests,
)
from services.eslint.run_eslint_fix import run_eslint_fix
from services.github.comments.create_comment import create_comment
from services.git.write_and_commit_file import write_and_commit_file
from services.eslint.get_eslint_config import get_eslint_config
from services.github.files.get_raw_content import get_raw_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.types.base_args import BaseArgs
from services.jest.format_coverage_comment import format_coverage_comment
from services.jest.run_jest_test import run_jest_test
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.node.ensure_tsconfig_relaxed_for_tests import (
    ensure_tsconfig_relaxed_for_tests,
)
from services.phpunit.run_phpunit_test import run_phpunit_test
from services.prettier.run_prettier_fix import run_prettier_fix
from services.tsc.create_tsc_issue import create_tsc_issue
from services.tsc.run_tsc_check import run_tsc_check
from utils.error.handle_exceptions import handle_exceptions
from utils.files.filter_js_ts_files import filter_js_ts_files
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@dataclass
class VerifyTaskIsCompleteResult:
    success: bool
    message: str
    fixes_applied: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)


@handle_exceptions(
    default_return_value=VerifyTaskIsCompleteResult(
        success=False,
        message="Verification failed due to an unexpected error.",
    ),
    raise_on_error=False,
)
async def verify_task_is_complete(
    base_args: BaseArgs, run_phpunit: bool = False, **_kwargs
):
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    pr_number = base_args.get("pr_number")
    token = base_args.get("token", "")
    new_branch = base_args.get("new_branch", "")

    if not pr_number:
        raise ValueError(
            f"pr_number is required for verify_task_is_complete but got: {pr_number}"
        )

    pr_files = get_pull_request_files(
        owner=owner, repo=repo, pr_number=pr_number, token=token
    )

    if not pr_files:
        logger.info(
            "No PR file changes found (e.g. setup handler determined no workflows needed), skipping checks"
        )
        return VerifyTaskIsCompleteResult(
            success=True, message="Task completed. No changes were needed."
        )

    js_test_files = [
        f["filename"]
        for f in pr_files
        if f["filename"].endswith(JS_TEST_FILE_EXTENSIONS) and f["status"] != "removed"
    ]

    ts_test_files = [f for f in js_test_files if f.endswith(TS_TEST_FILE_EXTENSIONS)]
    if ts_test_files:
        clone_dir = base_args.get("clone_dir", "")
        root_files = [
            f
            for f in os.listdir(clone_dir)
            if os.path.isfile(os.path.join(clone_dir, f))
        ]

        tsconfig_path, _ = ensure_tsconfig_relaxed_for_tests(
            root_files=root_files,
            base_args=base_args,
        )
        if tsconfig_path:
            ensure_jest_uses_tsconfig_for_tests(
                root_files=root_files,
                base_args=base_args,
                tsconfig_path=tsconfig_path,
            )

    if js_test_files:
        eslint_config = get_eslint_config(base_args)
        if eslint_config:
            ensure_eslint_relaxed_for_tests(
                eslint_config=eslint_config, base_args=base_args
            )

    non_removed_files = [f["filename"] for f in pr_files if f["status"] != "removed"]
    js_ts_files = filter_js_ts_files(non_removed_files)

    formatting_applied: list[str] = []
    remaining_errors: list[str] = []
    error_files: set[str] = set()
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
            write_and_commit_file(
                file_content=prettier_result.content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Format {file_path} with Prettier",
            )
            content = prettier_result.content
            formatting_applied.append(f"- {file_path}: Prettier")
        if prettier_result.error:
            remaining_errors.append(f"- {file_path}: Prettier: {prettier_result.error}")
            error_files.add(file_path)

        eslint_result = await run_eslint_fix(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if eslint_result.content and eslint_result.content != content:
            write_and_commit_file(
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
            error_files.add(file_path)

    if formatting_applied:
        logger.info("Applied formatting to files:\n%s", "\n".join(formatting_applied))

    # Run tsc type check on all non-removed files
    tsc_result = await run_tsc_check(base_args=base_args, file_paths=non_removed_files)
    if tsc_result.errors:
        baseline = base_args.get("baseline_tsc_errors", set())
        pr_file_set = {f["filename"] for f in pr_files}
        unrelated_tsc_errors: list[str] = []
        for err in tsc_result.errors:
            # Extract file path from tsc error format "file(line,col): error ..."
            err_file = err.split("(")[0] if "(" in err else ""
            if err_file in pr_file_set:
                # Always report errors in PR files (agent must fix these)
                remaining_errors.append(f"- tsc: {err}")
                error_files.add(err_file)
            elif err in baseline:
                # Pre-existing error in non-PR file, skip
                unrelated_tsc_errors.append(err)
            else:
                # New error in non-PR file, might be caused by PR changes
                remaining_errors.append(f"- tsc: {err}")
        if unrelated_tsc_errors:
            logger.info(
                "tsc: %d pre-existing errors skipped (not in PR files)",
                len(unrelated_tsc_errors),
            )
            create_tsc_issue(base_args=base_args, unrelated_errors=unrelated_tsc_errors)

    # Set by new_pr_handler for schedule PRs so run_jest_test collects coverage using Istanbul instead of V8.
    impl_file_to_collect_coverage_from = base_args.get(
        "impl_file_to_collect_coverage_from", ""
    )

    # Run jest/vitest tests on test files (with -u to auto-update stale snapshots)
    jest_result = await run_jest_test(
        base_args=base_args,
        test_file_paths=js_test_files,
        impl_file_to_collect_coverage_from=impl_file_to_collect_coverage_from,
    )
    if jest_result.errors:
        for err in jest_result.errors:
            remaining_errors.append(f"- {jest_result.runner_name}: {err}")
        error_files.update(jest_result.error_files)

    # Post coverage results as PR comment and check for incomplete coverage
    if jest_result.coverage and not jest_result.errors:
        cov = jest_result.coverage
        if cov.error:
            logger.warning("coverage: %s (not fixable by agent, skipping)", cov.error)
        else:
            comment_body = format_coverage_comment(
                cov, impl_file_to_collect_coverage_from
            )
            create_comment(body=comment_body, base_args=base_args)

            has_incomplete_coverage = (
                cov.statement_pct < 100
                or cov.branch_pct < 100
                or cov.function_pct < 100
                or cov.line_pct < 100
            )
            if has_incomplete_coverage:
                remaining_errors.append(f"- coverage:\n{comment_body}")
                error_files.update(js_test_files)

    # Commit any snapshot files updated by jest -u
    clone_dir = base_args.get("clone_dir", "")
    for snap_path in jest_result.updated_snapshots:
        snap_content = read_local_file(file_path=snap_path, base_dir=clone_dir)
        if not snap_content:
            continue
        write_and_commit_file(
            file_content=snap_content,
            file_path=snap_path,
            base_args=base_args,
            commit_message=f"Update snapshot {snap_path}",
        )
        formatting_applied.append(f"- {snap_path}: Snapshot updated")

    # PHPUnit disabled by default: tests fail due to Lambda environment limitations
    if run_phpunit:
        php_test_files = [
            f["filename"]
            for f in pr_files
            if f["filename"].endswith(PHP_TEST_FILE_EXTENSIONS)
            and f["status"] != "removed"
        ]
        phpunit_result = await run_phpunit_test(
            base_args=base_args,
            test_file_paths=php_test_files,
        )
        if phpunit_result.errors:
            for err in phpunit_result.errors:
                remaining_errors.append(f"- phpunit: {err}")
            error_files.update(phpunit_result.error_files)

    if remaining_errors:
        error_msg = "\n".join(remaining_errors)
        logger.warning("Remaining errors after fixes:\n%s", error_msg)
        return VerifyTaskIsCompleteResult(
            success=False,
            message=f"Task NOT complete. Fix these errors:\n{error_msg}",
            fixes_applied=formatting_applied,
            error_files=error_files,
        )

    return VerifyTaskIsCompleteResult(
        success=True,
        message="Task completed.",
        fixes_applied=formatting_applied,
    )

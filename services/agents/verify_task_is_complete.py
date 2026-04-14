import os
from dataclasses import dataclass, field

from anthropic.types import ToolUnionParam

from constants.files import (
    JS_TEST_FILE_EXTENSIONS,
    PHP_TEST_FILE_EXTENSIONS,
    TS_TEST_FILE_EXTENSIONS,
)
from constants.node import FALLBACK_NODE_VERSION
from services.agents.run_quality_gate import QUALITY_GATE_MESSAGE, run_quality_gate
from services.eslint.ensure_eslint_relaxed_for_tests import (
    ensure_eslint_relaxed_for_tests,
)
from services.eslint.run_eslint_fix import run_eslint_fix
from services.github.comments.create_comment import create_comment
from services.git.write_and_commit_file import write_and_commit_file
from services.eslint.get_eslint_config import get_eslint_config
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.types.base_args import BaseArgs
from services.jest.format_coverage_comment import format_coverage_comment
from services.jest.run_jest_test import run_jest_test
from services.node.detect_node_version import detect_node_version
from services.node.ensure_jest_timeout_for_ci import ensure_jest_timeout_for_ci
from services.node.ensure_jest_uses_tsconfig_for_tests import (
    ensure_jest_uses_tsconfig_for_tests,
)
from services.node.ensure_tsconfig_relaxed_for_tests import (
    ensure_tsconfig_relaxed_for_tests,
)
from services.node.ensure_vitest_timeout_for_ci import ensure_vitest_timeout_for_ci
from services.node.switch_node_version import switch_node_version
from services.phpunit.run_phpunit_test import run_phpunit_test
from services.prettier.run_prettier_fix import run_prettier_fix
from services.pytest.run_pytest_test import run_pytest_test
from services.slack.slack_notify import slack_notify
from services.tsc.create_tsc_issue import create_tsc_issue
from services.tsc.run_tsc_check import run_tsc_check
from utils.error.handle_exceptions import handle_exceptions
from utils.files.filter_js_ts_files import filter_js_ts_files
from utils.files.is_python_test_file import is_python_test_file
from utils.files.is_source_file import is_source_file
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger
from utils.logs.detect_infra_failure import detect_infra_failure

# See https://docs.anthropic.com/en/docs/build-with-claude/tool-use#defining-tools
# No parameters needed - agent calls with empty {} (JSON Schema requires the object structure)
# In API payload: verify_task_is_complete({}) - the empty object must be explicitly sent
# Conceptually equivalent to verify_task_is_complete() - a function with no arguments
VERIFY_TASK_IS_COMPLETE: ToolUnionParam = {
    "name": "verify_task_is_complete",
    "description": "Call this when you have finished making all required changes for the ENTIRE original issue - not after just one step. You MUST call this to complete the task - do not just stop calling tools.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


@dataclass
class VerifyTaskIsCompleteResult:
    success: bool
    message: str
    fixes_applied: list[str] = field(default_factory=list)
    error_files: set[str] = field(default_factory=set)
    modified_files: set[str] = field(default_factory=set)


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
    clone_dir = base_args.get("clone_dir", "")
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    pr_number = base_args.get("pr_number")
    token = base_args.get("token", "")

    if not pr_number:
        raise ValueError(
            f"pr_number is required for verify_task_is_complete but got: {pr_number}"
        )

    pr_files = get_pull_request_files(
        owner=owner, repo=repo, pr_number=pr_number, token=token
    )

    trigger = base_args.get("trigger", "")
    impl_file = base_args.get("impl_file_to_collect_coverage_from", "")

    quality_gate_fail_count = base_args["quality_gate_fail_count"]

    if not pr_files:
        # 0 changes on a schedule/dashboard PR: fail immediately without LLM call.
        # The schedule_handler already evaluated quality and found issues (that's why it created the PR). The LLM quality gate only runs after the agent makes changes (bottom of this function) to avoid paying for the same evaluation twice.
        if trigger in ("schedule", "dashboard") and impl_file:
            # First 0-change attempt: reject to nudge agent to try.
            # Second 0-change attempt: agent genuinely can't improve, let it pass.
            if quality_gate_fail_count < 1:
                base_args["quality_gate_fail_count"] = quality_gate_fail_count + 1
                return VerifyTaskIsCompleteResult(
                    success=False,
                    message=f"Task NOT complete. You made 0 changes to the test file for {impl_file}. {QUALITY_GATE_MESSAGE}",
                )

            logger.info(
                "Agent retried with 0 changes for %s, allowing completion", impl_file
            )

        logger.info("No PR file changes found, skipping file checks")
        return VerifyTaskIsCompleteResult(
            success=True, message="Task completed. No changes were needed."
        )

    formatting_applied: list[str] = []
    remaining_errors: list[str] = []
    error_files: set[str] = set()
    modified_files: set[str] = set()

    js_test_files = [
        f["filename"]
        for f in pr_files
        if f["filename"].endswith(JS_TEST_FILE_EXTENSIONS) and f["status"] != "removed"
    ]

    if js_test_files:
        # Switch Node.js to the version the repo requires (no-op if already matching default)
        detected_node = detect_node_version(clone_dir)
        if detected_node != FALLBACK_NODE_VERSION:
            switch_node_version(version=detected_node, base_args=base_args)

        root_files = [
            f
            for f in os.listdir(clone_dir)
            if os.path.isfile(os.path.join(clone_dir, f))
        ]

        ts_test_files = [
            f for f in js_test_files if f.endswith(TS_TEST_FILE_EXTENSIONS)
        ]
        if ts_test_files:
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

        eslint_config = get_eslint_config(base_args)
        if eslint_config:
            ensure_eslint_relaxed_for_tests(
                eslint_config=eslint_config, base_args=base_args
            )
        jest_config = ensure_jest_timeout_for_ci(
            root_files=root_files, base_args=base_args
        )
        if jest_config:
            modified_files.add(jest_config)
        vitest_config = ensure_vitest_timeout_for_ci(
            root_files=root_files, base_args=base_args
        )
        if vitest_config:
            modified_files.add(vitest_config)

    non_removed_files = [f["filename"] for f in pr_files if f["status"] != "removed"]
    js_ts_files = filter_js_ts_files(non_removed_files)

    for file_path in js_ts_files:
        content = read_local_file(file_path=file_path, base_dir=clone_dir)
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

    # Always pass source files so jest --findRelatedTests can discover dependent tests
    # (e.g., dead code removal from a source file may break tests not in the PR).
    jest_result = await run_jest_test(
        base_args=base_args,
        test_file_paths=js_test_files,
        source_file_paths=[f for f in js_ts_files if is_source_file(f)],
        impl_file_to_collect_coverage_from=impl_file_to_collect_coverage_from,
    )
    if jest_result.errors:
        combined_errors = "\n".join(jest_result.errors)
        infra_failure = detect_infra_failure(combined_errors)
        if infra_failure:
            logger.warning(
                "Jest infra failure detected (%s), skipping errors", infra_failure
            )
        else:
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

    py_test_files = [
        f["filename"]
        for f in pr_files
        if is_python_test_file(f["filename"]) and f["status"] != "removed"
    ]
    pytest_result = await run_pytest_test(
        base_args=base_args,
        test_file_paths=py_test_files,
    )
    if pytest_result.errors:
        for err in pytest_result.errors:
            remaining_errors.append(f"- pytest: {err}")
        error_files.update(pytest_result.error_files)

    # Quality gate for schedule/dashboard PRs: evaluate test quality via Claude.
    # Runs last to avoid paying for LLM call when lint/test errors will force a retry anyway.
    # Escape hatch: skip after 3 consecutive failures to prevent infinite loops.
    if trigger in ("schedule", "dashboard") and impl_file and not remaining_errors:
        if quality_gate_fail_count >= 3:
            logger.info(
                "Quality gate skipped for %s: failed %d times, accepting current quality",
                impl_file,
                quality_gate_fail_count,
            )
            pr_number = base_args.get("pr_number", 0)
            thread_ts = base_args.get("slack_thread_ts")
            slack_notify(
                f"Quality gate skipped for {owner}/{repo}#{pr_number} ({impl_file}): "
                f"failed {quality_gate_fail_count} times, accepting current quality",
                thread_ts,
            )
        else:
            quality_error = run_quality_gate(
                clone_dir=clone_dir, impl_file=impl_file, base_args=base_args
            )
            if quality_error:
                base_args["quality_gate_fail_count"] = quality_gate_fail_count + 1
                remaining_errors.append(f"- {quality_error}")

    if remaining_errors:
        error_msg = "\n".join(remaining_errors)
        logger.warning("Remaining errors after fixes:\n%s", error_msg)
        return VerifyTaskIsCompleteResult(
            success=False,
            message=f"Task NOT complete. Fix these errors:\n{error_msg}",
            fixes_applied=formatting_applied,
            error_files=error_files,
            modified_files=modified_files,
        )

    return VerifyTaskIsCompleteResult(
        success=True,
        message="Task completed.",
        fixes_applied=formatting_applied,
        modified_files=modified_files,
    )

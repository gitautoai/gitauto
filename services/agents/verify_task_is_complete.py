# Local imports
from services.eslint.run_eslint import run_eslint
from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import BaseArgs
from services.node.ensure_tsconfig_for_tests import ensure_tsconfig_for_tests
from services.prettier.run_prettier import run_prettier
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.syntax.fix_missing_braces import fix_missing_braces

TS_TEST_FILE_EXTENSIONS = (
    ".test.ts",
    ".test.tsx",
    ".spec.ts",
    ".spec.tsx",
)

JS_TEST_FILE_EXTENSIONS = (
    ".test.js",
    ".test.jsx",
    ".spec.js",
    ".spec.jsx",
) + TS_TEST_FILE_EXTENSIONS

JS_TS_FILE_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx")


@handle_exceptions(
    default_return_value={"success": True, "message": "Task completed."},
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
        return {
            "success": False,
            "message": "Error: Cannot complete task - the PR has no changes. You must make actual code changes before calling verify_task_is_complete. Use apply_diff_to_file or replace_remote_file_content to commit your changes first.",
        }

    js_test_files = [
        f["filename"]
        for f in pr_files
        if f["filename"].endswith(JS_TEST_FILE_EXTENSIONS) and f["status"] != "removed"
    ]

    ts_test_files = [f for f in js_test_files if f.endswith(TS_TEST_FILE_EXTENSIONS)]
    if ts_test_files:
        ensure_tsconfig_for_tests(
            base_args=base_args,
            commit_message="Add tsconfig.test.json for relaxed test file checking",
        )

    fixes_applied: list[str] = []
    for file_path in js_test_files:
        content = get_raw_content(
            owner=owner, repo=repo, file_path=file_path, ref=new_branch, token=token
        )
        if not content:
            continue

        result = fix_missing_braces(content)
        if result["fixes"]:
            upload_result = replace_remote_file_content(
                file_content=result["content"],
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Fix missing braces in {file_path}",
            )
            if upload_result:
                for item in result["fixes"]:
                    if "missing" in item:
                        fixes_applied.append(
                            f"- {file_path}: Inserted '{item['missing']}' after line {item['insert_after_line']} for {item['block_type']} block."
                        )
                    else:
                        fixes_applied.append(
                            f"- {file_path}: Removed stray '{item['removed_content']}' from line {item['removed_line']}."
                        )

    if fixes_applied:
        logger.info("Fixed missing braces in test files:\n%s", "\n".join(fixes_applied))

    js_ts_files = [
        f["filename"]
        for f in pr_files
        if f["filename"].endswith(JS_TS_FILE_EXTENSIONS) and f["status"] != "removed"
    ]

    formatting_applied: list[str] = []
    for file_path in js_ts_files:
        original_content = get_raw_content(
            owner=owner, repo=repo, file_path=file_path, ref=new_branch, token=token
        )
        if not original_content:
            continue

        content = original_content

        prettier_result = await run_prettier(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if prettier_result:
            content = prettier_result

        eslint_result = await run_eslint(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if eslint_result:
            content = eslint_result

        if content != original_content:
            replace_remote_file_content(
                file_content=content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Format {file_path}",
            )
            formatting_applied.append(f"- {file_path}")

    if formatting_applied:
        logger.info("Applied formatting to files:\n%s", "\n".join(formatting_applied))

    return {"success": True, "message": "Task completed."}

# Local imports
from services.github.files.get_raw_content import get_raw_content
from services.github.pulls.get_pull_request_files import get_pull_request_files
from services.github.types.github_types import BaseArgs
from utils.error.handle_exceptions import handle_exceptions
from utils.syntax.detect_missing_braces import detect_missing_braces

JS_TEST_FILE_EXTENSIONS = (
    ".test.js",
    ".test.jsx",
    ".test.ts",
    ".test.tsx",
    ".spec.js",
    ".spec.jsx",
    ".spec.ts",
    ".spec.tsx",
)


@handle_exceptions(
    default_return_value={"success": True, "message": "Task completed."},
    raise_on_error=False,
)
def verify_task_is_complete(base_args: BaseArgs, **_kwargs):
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

    syntax_errors: list[str] = []
    for file_path in js_test_files:
        content = get_raw_content(
            owner=owner, repo=repo, file_path=file_path, ref=new_branch, token=token
        )
        if not content:
            continue

        missing_braces = detect_missing_braces(content)
        if missing_braces:
            for item in missing_braces:
                syntax_errors.append(
                    f"- {file_path}: Missing '{item['missing']}' for {item['block_type']} block starting at line {item['block_start_line']}. Insert after line {item['insert_after_line']}."
                )

    if syntax_errors:
        error_list = "\n".join(syntax_errors)
        return {
            "success": False,
            "message": f"Error: Syntax errors detected in test files. Fix these missing closing braces before completing:\n{error_list}",
        }

    return {
        "success": True,
        "message": "Task completed successfully. PR has changes.",
    }

from dataclasses import dataclass, field

from services.eslint.run_eslint_fix import run_eslint_fix
from services.github.commits.replace_remote_file import replace_remote_file_content
from services.github.files.get_raw_content import get_raw_content
from services.github.types.github_types import BaseArgs
from services.prettier.run_prettier_fix import run_prettier_fix
from services.tsc.run_tsc_check import run_tsc_check
from utils.error.handle_exceptions import handle_exceptions
from utils.files.filter_js_ts_files import filter_js_ts_files
from utils.logging.logging_config import logger


@dataclass
class VerifyTaskIsReadyResult:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    files_with_errors: set[str] = field(default_factory=set)


@handle_exceptions(
    default_return_value=VerifyTaskIsReadyResult(),
    raise_on_error=False,
)
async def verify_task_is_ready(
    *, base_args: BaseArgs, file_paths: list[str], run_tsc: bool = False
) -> VerifyTaskIsReadyResult:
    owner = base_args.get("owner", "")
    repo = base_args.get("repo", "")
    token = base_args.get("token", "")
    base_branch = base_args.get("base_branch", "")

    js_ts_files = filter_js_ts_files(file_paths)
    if not js_ts_files:
        return VerifyTaskIsReadyResult()

    errors: list[str] = []
    formatting_applied: list[str] = []
    files_with_errors: set[str] = set()
    for file_path in js_ts_files:
        content = get_raw_content(
            owner=owner, repo=repo, file_path=file_path, ref=base_branch, token=token
        )
        if not content:
            continue

        prettier_result = await run_prettier_fix(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        if prettier_result.error:
            errors.append(f"- {file_path}: Prettier: {prettier_result.error}")
            files_with_errors.add(file_path)
            logger.warning(
                "Prettier failed on %s: %s", file_path, prettier_result.error
            )
        elif prettier_result.content and prettier_result.content != content:
            replace_remote_file_content(
                file_content=prettier_result.content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Format {file_path} with Prettier",
            )
            content = prettier_result.content
            formatting_applied.append(f"- {file_path}: Prettier")

        eslint_result = await run_eslint_fix(
            base_args=base_args,
            file_path=file_path,
            file_content=content,
        )
        # Push partial fixes even if errors remain
        if eslint_result.content and eslint_result.content != content:
            replace_remote_file_content(
                file_content=eslint_result.content,
                file_path=file_path,
                base_args=base_args,
                commit_message=f"Lint {file_path} with ESLint",
            )
            formatting_applied.append(f"- {file_path}: ESLint")
        # Report remaining unfixable errors
        if eslint_result.error:
            errors.append(f"- {file_path}: ESLint: {eslint_result.error}")
            files_with_errors.add(file_path)
            logger.warning("ESLint failed on %s: %s", file_path, eslint_result.error)

    if formatting_applied:
        logger.info("Applied formatting to files:\n%s", "\n".join(formatting_applied))

    # Run tsc type check if requested (for check_suite and review handlers)
    if run_tsc:
        tsc_result = await run_tsc_check(base_args=base_args, file_paths=file_paths)
        if tsc_result.errors:
            for err in tsc_result.errors:
                errors.append(f"- tsc: {err}")
            files_with_errors.update(tsc_result.error_files)

    if errors:
        return VerifyTaskIsReadyResult(
            success=False,
            errors=errors,
            fixes_applied=formatting_applied,
            files_with_errors=files_with_errors,
        )

    return VerifyTaskIsReadyResult(fixes_applied=formatting_applied)

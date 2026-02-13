import json
import os
import subprocess
from dataclasses import dataclass
from typing import TypedDict

import sentry_sdk

from config import UTF8
from constants.aws import EFS_TIMEOUT_SECONDS
from services.eslint.eslint_config_has_parser_project import (
    eslint_config_has_parser_project,
)
from services.github.files.get_eslint_config import get_eslint_config
from services.github.types.github_types import BaseArgs
from services.node.get_npm_cache_dir import set_npm_cache_env
from utils.error.handle_exceptions import handle_exceptions
from utils.files.is_source_file import is_source_file
from utils.logging.logging_config import logger


class ESLintMessage(TypedDict, total=False):
    line: int
    column: int
    message: str
    ruleId: str
    fatal: bool


class ESLintFileResult(TypedDict):
    messages: list[ESLintMessage]


# Rules relevant to coverage/testability (dead code, unreachable code, parsing errors).
# Style-only rules like no-explicit-any that --fix can't resolve don't affect coverage.
COVERAGE_RELEVANT_RULES = {
    "@typescript-eslint/no-unnecessary-condition",
    "no-unreachable",
}


@dataclass
class ESLintResult:
    success: bool
    content: str | None
    lint_errors: str | None
    coverage_errors: str | None


@handle_exceptions(
    default_return_value=ESLintResult(
        success=True, content=None, lint_errors=None, coverage_errors=None
    ),
    raise_on_error=False,
)
async def run_eslint_fix(*, base_args: BaseArgs, file_path: str, file_content: str):
    if not file_content.strip():
        logger.info("ESLint: Skipping %s - empty content", file_path)
        return ESLintResult(
            success=True, content=None, lint_errors=None, coverage_errors=None
        )

    if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        logger.info("ESLint: Skipping %s - not a JS/TS file", file_path)
        return ESLintResult(
            success=True, content=None, lint_errors=None, coverage_errors=None
        )

    eslint_config = get_eslint_config(base_args)
    if not eslint_config:
        logger.info("ESLint: Skipping %s - no ESLint config found in repo", file_path)
        return ESLintResult(
            success=True, content=None, lint_errors=None, coverage_errors=None
        )

    config_filename = eslint_config.get("filename", "")
    is_legacy_config = config_filename.startswith(".eslintrc")

    clone_dir = base_args.get("clone_dir", "")

    # Write to disk and use --fix (alternative: stdin/stdout without file)
    full_path = os.path.join(clone_dir, file_path)
    os.makedirs(
        os.path.dirname(full_path), exist_ok=True
    )  # For new files in new directories

    with open(full_path, "w", encoding=UTF8) as f:
        f.write(file_content)

    env = os.environ.copy()
    set_npm_cache_env(env)

    # ESLint 9+ uses flat config (eslint.config.js) by default
    # For repos using legacy .eslintrc.* config, disable flat config mode
    if is_legacy_config:
        env["ESLINT_USE_FLAT_CONFIG"] = "false"
        logger.info("ESLint: Using legacy config mode for %s", config_filename)

    # Check if eslint exists locally before running npx
    eslint_bin = os.path.join(clone_dir, "node_modules", ".bin", "eslint")
    eslint_exists = os.path.exists(eslint_bin)
    logger.info(
        "ESLint: Local binary exists=%s at %s",
        eslint_exists,
        eslint_bin,
    )

    # Check if we can enable typed linting for unreachable code detection
    tsconfig_exists = os.path.exists(os.path.join(clone_dir, "tsconfig.json"))
    ts_eslint_plugin = os.path.exists(
        os.path.join(clone_dir, "node_modules", "@typescript-eslint", "eslint-plugin")
    )
    ts_eslint_parser = os.path.exists(
        os.path.join(clone_dir, "node_modules", "@typescript-eslint", "parser")
    )
    # Typed linting is only for source files (dead code detection for coverage).
    # Non-source files are typically excluded from tsconfig.json, which causes
    # ESLint to fail entirely (losing all linting including --fix).
    can_use_typed_linting = (
        tsconfig_exists
        and ts_eslint_plugin
        and ts_eslint_parser
        and is_source_file(file_path)
    )

    # Build ESLint command
    # --no-warn-ignored: Suppress "File ignored because of a matching ignore pattern" warnings.
    # Without this, ignored files produce a JSON message with no ruleId that gets misclassified as a lint error, causing the agent to loop trying to fix it.
    cmd = ["npx", "--yes", "eslint", "--fix", "--format", "json", "--no-warn-ignored"]
    if can_use_typed_linting:
        cmd.extend(
            [
                "--rule",
                "@typescript-eslint/no-unnecessary-condition: error",
            ]
        )
        # Only add --parser-options if the repo's ESLint config doesn't already specify a project. CLI --parser-options overrides config file settings, which breaks repos that use a dedicated tsconfig for linting (e.g., tsconfig.eslint.json).
        if not eslint_config_has_parser_project(eslint_config):
            cmd.extend(["--parser-options", "project:tsconfig.json"])
        logger.info("ESLint: Typed linting enabled for unreachable code detection")
    cmd.append(full_path)

    # --yes: fallback to download if not in node_modules
    logger.info("ESLint: Running eslint with --fix...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EFS_TIMEOUT_SECONDS,
        check=False,
        cwd=clone_dir,
        env=env,
    )

    # ESLint exit codes:
    # 0 = no linting errors
    # 1 = linting errors found (some fixable, some not)
    # 2+ = fatal error (bad config, missing file, crash)
    if result.returncode >= 2:
        error_msg = result.stderr.strip() or "Fatal ESLint error"
        logger.warning("ESLint failed for %s: %s", file_path, error_msg)
        return ESLintResult(
            success=False, content=None, lint_errors=error_msg, coverage_errors=None
        )

    with open(full_path, "r", encoding=UTF8) as f:
        fixed_content = f.read()

    lint_errors: list[str] = []
    coverage_errors: list[str] = []
    if result.stdout:
        try:
            eslint_output: list[ESLintFileResult] = json.loads(result.stdout)
            for file_result in eslint_output:
                for message in file_result.get("messages", []):
                    line = message.get("line", "?")
                    msg = message.get("message", "Unknown error")
                    rule_id = message.get("ruleId", "")
                    rule_suffix = f" ({rule_id})" if rule_id else ""
                    error_str = f"Line {line}: {msg}{rule_suffix}"
                    if rule_id in COVERAGE_RELEVANT_RULES:
                        coverage_errors.append(error_str)
                    else:
                        lint_errors.append(error_str)
        except json.JSONDecodeError as e:
            sentry_sdk.capture_exception(e)

    if lint_errors or coverage_errors:
        all_errors = lint_errors + coverage_errors
        logger.warning(
            "ESLint: Remaining errors in %s: %s", file_path, "; ".join(all_errors)
        )
        return ESLintResult(
            success=False,
            content=fixed_content,
            lint_errors="; ".join(lint_errors) if lint_errors else None,
            coverage_errors="; ".join(coverage_errors) if coverage_errors else None,
        )

    logger.info("ESLint: Successfully fixed %s", file_path)
    return ESLintResult(
        success=True, content=fixed_content, lint_errors=None, coverage_errors=None
    )

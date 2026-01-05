import json
import os
import subprocess
import tempfile

import sentry_sdk

from config import UTF8
from services.efs.get_efs_dir import get_efs_dir
from services.efs.is_efs_install_ready import is_efs_install_ready
from utils.error.handle_exceptions import handle_exceptions


def _default_eslint_result(file_content: str, **_):
    return {"success": True, "fixed_content": file_content, "errors": []}


@handle_exceptions(default_return_value=_default_eslint_result, raise_on_error=False)
def run_eslint(
    *,
    owner: str,
    repo: str,
    file_path: str,
    file_content: str,
    eslint_config_content: str,
    package_json_content: str | None = None,
):
    if not file_content.strip():
        print(f"ESLint: Skipping {file_path} - empty content")
        return _default_eslint_result(file_content=file_content)

    if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        print(f"ESLint: Skipping {file_path} - not a JS/TS file")
        return _default_eslint_result(file_content=file_content)

    if not package_json_content:
        print(f"ESLint: Skipping {file_path} - no package.json")
        return _default_eslint_result(file_content=file_content)

    if not is_efs_install_ready(owner, repo, "node"):
        raise RuntimeError(f"EFS install not ready for {owner}/{repo}")

    extension = os.path.splitext(file_path)[1]
    efs_dir = get_efs_dir(owner, repo)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, f"temp{extension}")
        with open(temp_file_path, "w", encoding=UTF8) as f:
            f.write(file_content)

        if eslint_config_content.strip().startswith("module.exports"):
            config_file_path = os.path.join(temp_dir, ".eslintrc.js")
        elif eslint_config_content.strip().startswith("export default"):
            config_file_path = os.path.join(temp_dir, "eslint.config.mjs")
        else:
            config_file_path = os.path.join(temp_dir, ".eslintrc.json")

        with open(config_file_path, "w", encoding=UTF8) as f:
            f.write(eslint_config_content)

        print("ESLint: Running eslint with --fix...")
        result = subprocess.run(
            [
                "npx",
                "--yes",
                "eslint",
                "--config",
                config_file_path,
                "--fix",
                "--format",
                "json",
                temp_file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            cwd=efs_dir,
        )

        # ESLint exit codes:
        # 0 = no linting errors
        # 1 = linting errors found (some fixable, some not)
        # 2+ = fatal error (bad config, missing file, crash)
        if result.returncode not in [0, 1]:
            raise RuntimeError(
                f"ESLint failed with code {result.returncode}: {result.stderr}"
            )

        with open(temp_file_path, "r", encoding=UTF8) as f:
            fixed_content = f.read()

        if result.stdout:
            try:
                eslint_output = json.loads(result.stdout)
                errors = []
                for file_result in eslint_output:
                    for message in file_result.get("messages", []):
                        errors.append(
                            {
                                "line": message.get("line"),
                                "column": message.get("column"),
                                "message": message.get("message"),
                                "ruleId": message.get("ruleId"),
                                "severity": message.get("severity"),
                            }
                        )

                if errors:
                    sentry_sdk.capture_message(
                        f"ESLint: {len(errors)} unfixable errors in {file_path}: {errors}",
                        level="warning",
                    )
                else:
                    print(f"ESLint: Successfully fixed {file_path} with no errors")

                return {
                    "success": len(errors) == 0,
                    "fixed_content": fixed_content,
                    "errors": errors,
                }
            except json.JSONDecodeError as e:
                # Capture but don't raise - we still want to return fixed_content
                sentry_sdk.capture_exception(e)

        print(f"ESLint: Completed for {file_path} (return code: {result.returncode})")
        return {
            "success": result.returncode == 0,
            "fixed_content": fixed_content,
            "errors": [],
        }

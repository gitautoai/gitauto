import json
import logging
import os
import subprocess
import tempfile

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def run_eslint(
    file_content: str,
    file_path: str,
    eslint_config_content: str,
    package_json_content: str | None = None,
):
    if not file_content.strip():
        print(f"ESLint: Skipping {file_path} - empty content")
        return {"success": True, "fixed_content": file_content, "errors": []}

    if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        print(f"ESLint: Skipping {file_path} - not a JS/TS file")
        return {"success": True, "fixed_content": file_content, "errors": []}

    extension = os.path.splitext(file_path)[1]

    eslint_version = "latest"
    packages_to_install = []

    if package_json_content:
        try:
            package_json = json.loads(package_json_content)
            all_deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {}),
            }

            for pkg, version in all_deps.items():
                if pkg == "eslint":
                    eslint_version = version.lstrip("^~>=")
                elif "eslint" in pkg.lower():
                    packages_to_install.append(f"{pkg}@{version.lstrip('^~>=')}")

            print(f"ESLint: Running for {file_path} with version {eslint_version}")
            print(f"ESLint: Installing {len(packages_to_install)} packages")
        except json.JSONDecodeError as e:
            logging.warning("ESLint: Failed to parse package.json: %s", e)
    else:
        print(f"ESLint: Running for {file_path} with latest version (no package.json)")

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

        if packages_to_install:
            print("ESLint: Installing packages via npm...")
            npm_env = os.environ.copy()
            npm_env["npm_config_cache"] = "/tmp/.npm"
            npm_result = subprocess.run(
                ["npm", "install", "--no-save", "--prefix", temp_dir]
                + packages_to_install,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
                cwd=temp_dir,
                env=npm_env,
            )
            if npm_result.returncode != 0:
                logging.error(
                    "ESLint: npm install failed with code %d", npm_result.returncode
                )
                logging.error("ESLint: npm stderr: %s", npm_result.stderr[:500])
            else:
                print("ESLint: npm install completed successfully")

        print(f"ESLint: Running eslint@{eslint_version} with --fix...")
        result = subprocess.run(
            [
                "npx",
                "--yes",
                f"eslint@{eslint_version}",
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
            cwd=temp_dir,
        )

        if result.returncode not in [0, 1]:
            logging.error("ESLint: Failed with return code %d", result.returncode)
            logging.error("ESLint: stderr: %s", result.stderr[:500])

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
                    logging.warning(
                        "ESLint: Found %d unfixable errors in %s",
                        len(errors),
                        file_path,
                    )
                    for err in errors[:3]:
                        logging.warning(
                            "  Line %s: %s (%s)",
                            err["line"],
                            err["message"],
                            err["ruleId"],
                        )
                else:
                    print(f"ESLint: Successfully fixed {file_path} with no errors")

                return {
                    "success": len(errors) == 0,
                    "fixed_content": fixed_content,
                    "errors": errors,
                }
            except json.JSONDecodeError as e:
                logging.error("ESLint: Failed to parse JSON output: %s", e)
                logging.error("ESLint: stdout: %s", result.stdout[:500])

        print(f"ESLint: Completed for {file_path} (return code: {result.returncode})")
        return {
            "success": result.returncode == 0,
            "fixed_content": fixed_content,
            "errors": [],
        }

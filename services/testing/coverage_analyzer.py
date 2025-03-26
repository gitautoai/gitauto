import json
import os
import re
import subprocess
from utils.handle_exceptions import handle_exceptions

DEFAULT_COVERAGES = {"statement": 0, "function": 0, "branch": 0, "path": 0}


def run_command(local_path: str, command: str, env=None, use_shell=True):
    if env is None:
        env = os.environ.copy()

    return subprocess.run(
        args=command if use_shell else command.split(),
        cwd=local_path,
        shell=use_shell,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def setup_js_env(local_path: str, env=None) -> dict:
    """Set up JavaScript environment with proper PATH"""
    if env is None:
        env = os.environ.copy()

    # Debug logs
    print(f"Current PATH: {env.get('PATH', '')}")
    print(
        f"Checking if node_modules/.bin exists: {os.path.exists(f'{local_path}/node_modules/.bin')}"
    )
    if os.path.exists(f"{local_path}/node_modules/.bin"):
        print(
            f"Contents of node_modules/.bin: {os.listdir(f'{local_path}/node_modules/.bin')}"
        )

    # Add node_modules/.bin to PATH
    env["PATH"] = f"{local_path}/node_modules/.bin:{env.get('PATH', '')}"
    print(f"Updated PATH: {env['PATH']}")

    return env


@handle_exceptions(default_return_value=DEFAULT_COVERAGES, raise_on_error=False)
def calculate_python_coverage(local_path: str) -> dict[str, float]:
    # https://coverage.readthedocs.io/en/7.7.0/cmd.html#execution-coverage-run
    run_command(local_path, "coverage run -m pytest", use_shell=False)

    # "-" is used to write to stdout
    # https://coverage.readthedocs.io/en/7.7.0/cmd.html#json-reporting-coverage-json
    result = run_command(local_path, "coverage json -o -", use_shell=False)

    coverage_data = json.loads(result.stdout)
    print(f"coverage_data: {coverage_data}")
    totals = coverage_data.get("totals", {})
    return {
        "statement": totals.get("percent_covered", 0),
        "branch": totals.get("percent_covered_branches", 0),
        "function": totals.get("percent_covered_functions", 0),
        "path": 0,
    }


@handle_exceptions(default_return_value="npm")
def detect_package_manager(local_path: str) -> str:
    package_json = run_command(local_path, "cat package.json", use_shell=True).stdout
    if not package_json:
        return "npm"

    data = json.loads(package_json)
    if "packageManager" in data and "yarn" in data["packageManager"]:
        return "yarn"

    return (
        "yarn"
        if run_command(local_path, "test -f yarn.lock", use_shell=True).returncode == 0
        else "npm"
    )


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


def parse_coverage_report(output: str):
    reports = []
    current_package = None
    current_path = ""

    split_output = output.split("\n")
    total_lines = len(split_output)
    for i, line in enumerate(split_output):
        print(f"Parsing coverage report... {i}/{total_lines}", end="\r")

        # Skip header/footer separator lines
        if line.strip().startswith("--") or line.strip().endswith("--"):
            continue

        # Package name detection
        if line.startswith(">"):
            current_package = line.split(":test")[0].strip("> ")
            current_path = ""  # Reset current path for new package
            continue

        # Coverage data detection
        if "|" in line and line.count("|") == 5:
            parts = [p.strip() for p in strip_ansi(line).split("|")]
            # Skip header line
            if parts[1] == "% Stmts":
                continue
            if len(parts) >= 6:
                try:
                    path = parts[0].strip()

                    # Determine the level and full path
                    if path == "All files":
                        level = "repository"
                        full_path = f"/{current_package}" if current_package else "/"
                    elif (
                        not path.endswith(".js")
                        and not path.endswith(".ts")
                        and not path.endswith(".tsx")
                    ):
                        level = "directory"
                        current_path = path
                        full_path = (
                            f"/{current_package}/{path}"
                            if current_package
                            else f"/{path}"
                        )
                    else:
                        level = "file"
                        package_prefix = (
                            f"/{current_package}" if current_package else ""
                        )
                        full_path = (
                            f"{package_prefix}/{current_path}/{path}"
                            if current_path
                            else f"{package_prefix}/{path}"
                        )
                        full_path = full_path.replace("//", "/")

                    reports.append(
                        {
                            "package_name": current_package,
                            "level": level,
                            "full_path": full_path,
                            "statement_coverage": float(parts[1]),
                            "function_coverage": float(parts[3]),
                            "branch_coverage": float(parts[2]),
                            "line_coverage": float(parts[4]),
                            "uncovered_lines": parts[5],
                        }
                    )
                except ValueError:
                    print(f"Error parsing line: {line}")
                    continue

    print(f"reports:\n{json.dumps(reports, indent=2)}")
    return reports


@handle_exceptions(default_return_value=[], raise_on_error=False)
def calculate_js_ts_coverage(local_path: str) -> list[dict]:
    """https://jestjs.io/docs/cli#--coverageboolean"""
    # Detect "yarn" or "npm"
    print("Detecting package manager...")
    pkg_manager = detect_package_manager(local_path)
    if (
        pkg_manager == "yarn"
        and run_command(local_path, "which yarn", use_shell=True).returncode != 0
    ):
        run_command(local_path, "npm install -g yarn", use_shell=False)

    # Set up JavaScript environment once
    env = setup_js_env(local_path)

    # Install dependencies
    install_cmd = "yarn install" if pkg_manager == "yarn" else "npm install"
    print(f"Installing dependencies with `{install_cmd}`")
    run_command(local_path, install_cmd, env=env, use_shell=False)

    # Build before running tests
    build_cmd = "yarn build" if pkg_manager == "yarn" else "npm run build"
    print(f"Building with `{build_cmd}`")
    run_command(local_path, build_cmd, env=env, use_shell=False)

    # Run tests with coverage

    test_cmd = f"{pkg_manager} test"
    print(f"Running tests with `{test_cmd}`")
    result = run_command(local_path, test_cmd, env=env, use_shell=False)

    # If test script is not defined, try using jest directly
    if "no test specified" in result.stderr or "Missing script" in result.stderr:
        test_cmd = "yarn jest" if pkg_manager == "yarn" else "npx jest"
        print(f"Test script not found, trying: `{test_cmd}`")
        result = run_command(
            local_path, f"{test_cmd} --coverage --verbose", env=env, use_shell=False
        )

    result.stdout.split("\n")

    # Print error if any
    error_lines = result.stderr.split("\n")
    if len(error_lines) > 100:
        print("Jest error (truncated):")
        print("\n".join(error_lines[:50]))
        print("...")
        print("\n".join(error_lines[-50:]))
    else:
        print(f"Jest error:\n{result.stderr}")

    reports = parse_coverage_report(result.stdout)
    return reports


@handle_exceptions(
    default_return_value={"primary_language": None, **DEFAULT_COVERAGES},
    raise_on_error=False,
)
def calculate_test_coverage(local_path: str, languages: dict[str, int]):
    if not languages:
        return {"primary_language": None, **DEFAULT_COVERAGES}

    primary_language = max(languages.items(), key=lambda x: x[1])[0].lower()
    coverage = DEFAULT_COVERAGES.copy()

    if primary_language == "python":
        coverage = calculate_python_coverage(local_path)
    elif primary_language in ["javascript", "typescript"]:
        coverage = calculate_js_ts_coverage(local_path)
    # elif primary_language == "java":
    #     coverage = calculate_java_coverage(local_path)

    return coverage

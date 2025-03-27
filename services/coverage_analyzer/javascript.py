import json
import os
import re
from services.coverage_analyzer.types import CoverageReport
from utils.file_manager import run_command
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="npm")
def detect_package_manager(local_path: str) -> str:
    package_json = run_command(
        cwd=local_path, command="cat package.json", use_shell=True
    ).stdout
    if not package_json:
        return "npm"

    data = json.loads(package_json)
    if "packageManager" in data and "yarn" in data["packageManager"]:
        return "yarn"

    return (
        "yarn"
        if run_command(
            cwd=local_path, command="test -f yarn.lock", use_shell=True
        ).returncode
        == 0
        else "npm"
    )


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


def parse_coverage_report(output: str):
    """Parse coverage report and return a list of standardized coverage data."""
    reports: list[CoverageReport] = []
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
def calculate_js_ts_coverage(local_path: str):
    """https://jestjs.io/docs/cli#--coverageboolean"""
    # Detect "yarn" or "npm"
    print("Detecting package manager...")
    pkg_manager = detect_package_manager(local_path)
    if (
        pkg_manager == "yarn"
        and run_command(cwd=local_path, command="which yarn", use_shell=True).returncode
        != 0
    ):
        run_command(cwd=local_path, command="npm install -g yarn", use_shell=False)

    # Check initial directory state
    print("Initial directory state:")
    print(f"Working directory: {os.getcwd()}")
    print(f"Local path: {local_path}")
    print(f"Local path contents: {os.listdir(local_path)}")
    print(f"Root contents: {os.listdir('/')}")
    print(f"Temp contents: {os.listdir('/tmp')}")

    # Install dependencies
    install_cmd = (
        "yarn install --verbose" if pkg_manager == "yarn" else "npm install --verbose"
    )
    print(f"Installing dependencies with `{install_cmd}`")
    result = run_command(cwd=local_path, command=install_cmd, use_shell=True)

    # Check post-install directory state
    print("Post-install directory state:")
    print(f"Local path contents: {os.listdir(local_path)}")
    print(f"Temp contents: {os.listdir('/tmp')}")

    if result.stdout:
        print(f"Install output: {result.stdout}")

    # Check if node_modules is installed
    find_cmd = "find /tmp -name 'node_modules' -type d 2>/dev/null || echo 'No node_modules found'"
    node_modules = run_command(cwd="/", command=find_cmd, use_shell=True).stdout.strip()
    print(f"Found node_modules directories: {node_modules}")

    # Lambda environment info
    print("\nLambda environment:")
    print(
        f"Memory: {run_command(cwd="/", command="cat /proc/meminfo | grep MemTotal", use_shell=True).stdout}"
    )

    # Build before running tests
    build_cmd = "yarn build" if pkg_manager == "yarn" else "npm run build"
    print(f"Building with `{build_cmd}`")
    run_command(cwd=local_path, command=build_cmd, use_shell=False)

    # Run tests with coverage

    test_cmd = f"{pkg_manager} test"
    print(f"Running tests with `{test_cmd}`")
    result = run_command(cwd=local_path, command=test_cmd, use_shell=False)

    # If test script is not defined, try using jest directly
    if "no test specified" in result.stderr or "Missing script" in result.stderr:
        test_cmd = "yarn jest" if pkg_manager == "yarn" else "npx jest"
        print(f"Test script not found, trying: `{test_cmd}`")
        result = run_command(
            cwd=local_path, command=f"{test_cmd} --coverage --verbose", use_shell=False
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

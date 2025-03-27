import json
from services.coverage_analyzer.types import DEFAULT_COVERAGES
from utils.file_manager import run_command
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=DEFAULT_COVERAGES, raise_on_error=False)
def calculate_python_coverage(local_path: str) -> dict[str, float]:
    # https://coverage.readthedocs.io/en/7.7.0/cmd.html#execution-coverage-run
    run_command(cwd=local_path, command="coverage run -m pytest", use_shell=False)

    # "-" is used to write to stdout
    # https://coverage.readthedocs.io/en/7.7.0/cmd.html#json-reporting-coverage-json
    result = run_command(cwd=local_path, command="coverage json -o -", use_shell=False)

    coverage_data = json.loads(result.stdout)
    print(f"coverage_data: {coverage_data}")
    totals = coverage_data.get("totals", {})
    return {
        "statement": totals.get("percent_covered", 0),
        "branch": totals.get("percent_covered_branches", 0),
        "function": totals.get("percent_covered_functions", 0),
        "path": 0,
    }

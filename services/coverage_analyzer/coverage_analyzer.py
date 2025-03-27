from services.coverage_analyzer.dart import calculate_dart_coverage
from services.coverage_analyzer.javascript import calculate_js_ts_coverage
from services.coverage_analyzer.python import calculate_python_coverage
from services.coverage_analyzer.types import DEFAULT_COVERAGES
from utils.handle_exceptions import handle_exceptions


@handle_exceptions(
    default_return_value={"primary_language": None, **DEFAULT_COVERAGES},
    raise_on_error=False,
)
def calculate_test_coverage(local_path: str, languages: dict[str, int]):
    if not languages:
        return {"primary_language": None, **DEFAULT_COVERAGES}

    primary_language = max(languages.items(), key=lambda x: x[1])[0].lower()
    print(f"Primary language: {primary_language}")
    coverage = DEFAULT_COVERAGES.copy()

    if primary_language == "python":
        coverage = calculate_python_coverage(local_path)
    elif primary_language in ["javascript", "typescript"]:
        coverage = calculate_js_ts_coverage(local_path)
    elif primary_language == "dart":
        coverage = calculate_dart_coverage(local_path)

    return coverage

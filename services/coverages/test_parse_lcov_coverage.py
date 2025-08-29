from config import UTF8
from services.coverages.parse_lcov_coverage import parse_lcov_coverage


def test_parse_lcov_python_sample_exact_counts():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)

    assert len(result) == 330

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 260

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["statement_coverage"] == 73.17
    assert repo_coverage["function_coverage"] == 80.58
    assert repo_coverage["branch_coverage"] == 55.14
    assert repo_coverage["line_coverage"] == 73.17


def test_parse_lcov_python_sample_specific_file():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)
    file_level = [r for r in result if r["level"] == "file"]

    config_file = next((f for f in file_level if f["full_path"] == "config.py"), None)
    assert config_file is not None
    assert config_file["statement_coverage"] == 100.0
    assert config_file["function_coverage"] == 100.0
    assert config_file["branch_coverage"] == 100.0
    assert config_file["line_coverage"] == 100.0
    assert config_file["uncovered_lines"] == ""
    assert config_file["uncovered_functions"] == ""
    assert config_file["uncovered_branches"] == ""


def test_parse_lcov_javascript_sample_exact_counts():
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)

    assert len(result) == 407

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 305

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["statement_coverage"] == 3.58
    assert repo_coverage["function_coverage"] == 2.7
    assert repo_coverage["branch_coverage"] == 2.54
    assert repo_coverage["line_coverage"] == 3.58


def test_parse_lcov_javascript_sample_specific_file():
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)
    file_level = [r for r in result if r["level"] == "file"]

    if file_level:
        sample_file = file_level[0]
        assert sample_file["full_path"] is not None
        assert isinstance(sample_file["statement_coverage"], float)
        assert isinstance(sample_file["line_coverage"], float)

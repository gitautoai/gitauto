from config import UTF8
from services.coverages.parse_lcov_coverage import parse_lcov_coverage


def test_parse_lcov_python_sample_exact_counts():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    assert len(result) == 294

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 228

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["statement_coverage"] == 67.9
    assert repo_coverage["function_coverage"] == 80.0
    assert repo_coverage["branch_coverage"] == 55.1
    assert repo_coverage["line_coverage"] == 67.9
    assert repo_coverage["lines_covered"] == 3813
    assert repo_coverage["lines_total"] == 5616
    assert repo_coverage["functions_covered"] == 188
    assert repo_coverage["functions_total"] == 235
    assert repo_coverage["branches_covered"] == 1007
    assert repo_coverage["branches_total"] == 1828


def test_parse_lcov_python_sample_specific_file():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())
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

    result = parse_lcov_coverage(lcov_content, set())

    assert len(result) == 396

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 296

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["statement_coverage"] == 3.6
    assert repo_coverage["function_coverage"] == 2.7
    assert repo_coverage["branch_coverage"] == 2.5
    assert repo_coverage["line_coverage"] == 3.6
    assert repo_coverage["lines_covered"] == 141
    assert repo_coverage["lines_total"] == 3919
    assert repo_coverage["functions_covered"] == 40
    assert repo_coverage["functions_total"] == 1472
    assert repo_coverage["branches_covered"] == 43
    assert repo_coverage["branches_total"] == 1696


def test_parse_lcov_javascript_sample_specific_file():
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())
    file_level = [r for r in result if r["level"] == "file"]

    if file_level:
        sample_file = file_level[0]
        assert sample_file["full_path"] is not None
        assert isinstance(sample_file["statement_coverage"], float)
        assert isinstance(sample_file["line_coverage"], float)


def test_parse_lcov_dotnet_real():
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    assert len(result) > 0

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 22

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["function_coverage"] == 14.0  # Real value from .NET LCOV
    assert repo_coverage["statement_coverage"] == 30.3  # Real value from .NET LCOV
    assert repo_coverage["line_coverage"] == 30.3  # Real value from .NET LCOV
    assert repo_coverage["branch_coverage"] == 4.2  # Real value from .NET LCOV


def test_fn_parsing_python():
    """Test FN parsing for Python 3-part format using real LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FN lines are parsed correctly (3-part format)
    # Example: FN:12,16,get_env_var
    assert "FN:12,16,get_env_var" in lcov_content
    assert "FN:9,10,test_owner" in lcov_content

    result = parse_lcov_coverage(lcov_content, set())
    # Should parse without errors
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_python():
    """Test FNDA parsing for Python using real LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FNDA lines are parsed correctly
    # Example: FNDA:1,get_env_var
    assert "FNDA:1,get_env_var" in lcov_content

    result = parse_lcov_coverage(lcov_content, set())
    # Check that function coverage is calculated correctly
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 80.0


def test_fn_parsing_javascript():
    """Test FN parsing for JavaScript 2-part format using real LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FN lines are parsed correctly (2-part format)
    # Example: FN:7,GlobalError
    assert "FN:7,GlobalError" in lcov_content
    assert "FN:30,RootLayout" in lcov_content

    result = parse_lcov_coverage(lcov_content, set())
    # Should parse without errors
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_javascript():
    """Test FNDA parsing for JavaScript using real LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FNDA lines are parsed correctly
    # Example: FNDA:0,GlobalError
    assert "FNDA:0,GlobalError" in lcov_content

    result = parse_lcov_coverage(lcov_content, set())
    # Check that function coverage is calculated correctly
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 2.7


def test_fn_parsing_dotnet():
    """Test FN parsing for .NET with commas in function signatures using real LCOV file"""
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FN lines with commas are in the file
    # Example: FN:24,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)
    assert (
        "FN:24,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)"
        in lcov_content
    )
    assert (
        "FN:53,.ctor(Salida.Models.MicrosipContext,Microsip.Core.IParameter)"
        in lcov_content
    )

    result = parse_lcov_coverage(lcov_content, set())
    # Should parse without errors
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_dotnet():
    """Test FNDA parsing for .NET with commas in function signatures using real LCOV file"""
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FNDA lines with commas are parsed correctly
    # Example: FNDA:0,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)
    assert (
        "FNDA:0,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)"
        in lcov_content
    )
    assert (
        "FNDA:13,.ctor(Salida.Models.MicrosipContext,Microsip.Core.IParameter)"
        in lcov_content
    )

    result = parse_lcov_coverage(lcov_content, set())
    # Check that function coverage is calculated correctly
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 14.0


def test_fn_fnda_parsing_formats():
    # Test all FN/FNDA formats: 2-part, 3-part, and with commas
    test_lcov = """TN:
SF:/src/utils.js
FN:10,simpleFunction
FNDA:5,simpleFunction
FNF:1
FNH:1
DA:10,5
LH:1
LF:1
end_of_record
SF:/src/helpers.py
FN:20,25,pythonFunction
FNDA:3,pythonFunction
FNF:1
FNH:1
DA:20,3
LH:1
LF:1
end_of_record
SF:/src/services.cs
FN:30,.ctor(System.String,System.Int32)
FN:40,Method(List<Dictionary<string,object>>,bool)
FNDA:2,.ctor(System.String,System.Int32)
FNDA:0,Method(List<Dictionary<string,object>>,bool)
FNF:2
FNH:1
DA:30,2
DA:40,0
LH:1
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov, set())

    # Should parse successfully
    assert len(result) > 0

    # Check repository level
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 75.0

    # Check that all formats parsed correctly
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 3

    # JavaScript file (2-part format)
    js_file = next(f for f in files if "utils.js" in f["full_path"])
    assert js_file["function_coverage"] == 100.0

    # Python file (3-part format)
    py_file = next(f for f in files if "helpers.py" in f["full_path"])
    assert py_file["function_coverage"] == 100.0

    # C# file (commas in function names)
    cs_file = next(f for f in files if "services.cs" in f["full_path"])
    assert cs_file["function_coverage"] == 50.0


def test_typescript_utility_file_not_filtered():
    test_lcov = """TN:
SF:utils/get-random-item.ts
FN:1,getRandomItem
FNF:1
FNH:1
FNDA:1134,getRandomItem
DA:1,1134
DA:2,1134
LF:2
LH:2
BRF:0
BRH:0
end_of_record
TN:
"""

    result = parse_lcov_coverage(test_lcov, set())

    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert files[0]["full_path"] == "utils/get-random-item.ts"
    assert files[0]["function_coverage"] == 100.0
    assert files[0]["line_coverage"] == 100.0


def test_parse_lcov_gitauto_real_exact_counts():
    """Test parsing GitAuto repository LCOV file with exact file counts.

    This test verifies that the parser correctly filters out test files
    and produces the expected number of reports. It will fail if there's
    a bug in production causing incorrect file extraction.
    """
    with open("payloads/lcov/lcov-gitauto-20250922.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    # Total reports should be: files + directories + repository
    # Expected: 249 files + 72 directories + 1 repository = 322 total
    assert len(result) == 322

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 249

    directory_level = [r for r in result if r["level"] == "directory"]
    assert len(directory_level) == 72

    # Verify repository level exists
    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert isinstance(repo_coverage["statement_coverage"], float)
    assert isinstance(repo_coverage["line_coverage"], float)

    # Verify specific test files are correctly filtered out
    config_file = next((f for f in file_level if f["full_path"] == "config.py"), None)
    assert config_file is not None, "config.py should be included as a non-test file"

    # Verify legitimate files containing 'test' are kept (they're not actual test files)
    legitimate_files = [
        "utils/files/is_test_file.py",  # utility to detect test files
    ]

    for file_path in legitimate_files:
        file_found = next((f for f in file_level if f["full_path"] == file_path), None)
        assert (
            file_found is not None
        ), f"{file_path} should be included as a legitimate non-test file"


def test_parse_lcov_ts_foxden_tools():
    """Test parsing foxden-tools TypeScript LCOV file.

    This repo uses V8 coverage provider and has FN:(empty-report) format.
    The schedule handler was creating PRs for files with 100% coverage
    because the coverage report was not being parsed/ingested.
    """
    with open("payloads/lcov/lcov-ts-foxden-tools.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    assert len(result) == 101

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 81

    directory_level = [r for r in result if r["level"] == "directory"]
    assert len(directory_level) == 19

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["statement_coverage"] == 14.6
    assert repo_coverage["function_coverage"] == 22.6
    assert repo_coverage["branch_coverage"] == 58.8
    assert repo_coverage["line_coverage"] == 14.6
    assert repo_coverage["lines_covered"] == 1272
    assert repo_coverage["lines_total"] == 8738
    assert repo_coverage["functions_covered"] == 38
    assert repo_coverage["functions_total"] == 168
    assert repo_coverage["branches_covered"] == 161
    assert repo_coverage["branches_total"] == 274

    # Verify common.ts has 100% coverage (was incorrectly reported as 0%)
    common_file = next(
        (f for f in file_level if f["full_path"] == "src/utils/typeGuard/common.ts"),
        None,
    )
    assert common_file is not None, "common.ts should be in parsed results"
    assert common_file["statement_coverage"] == 100.0
    assert common_file["function_coverage"] == 100.0
    assert common_file["branch_coverage"] == 100.0


def test_tool_measures_all_metrics_zero_branches_upgraded_to_100():
    """Jest: tool measures branches (other files have branches), but this file has 0 branches → 100%"""
    test_lcov = """TN:
SF:src/utils/isJestRunning.ts
FN:1,isJestRunning
FNDA:1,isJestRunning
FNF:1
FNH:1
DA:1,1
DA:2,1
LF:2
LH:2
BRF:0
BRH:0
end_of_record
SF:src/utils/other.ts
FN:1,otherFunc
FNDA:1,otherFunc
FNF:1
FNH:1
DA:1,1
DA:2,1
LF:2
LH:2
BRDA:1,0,0,1
BRF:1
BRH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov, set())
    jest_file = next(
        r for r in result if r["full_path"] == "src/utils/isJestRunning.ts"
    )

    assert jest_file["line_coverage"] == 100.0
    assert jest_file["function_coverage"] == 100.0
    assert (
        jest_file["branch_coverage"] == 100
    )  # Upgraded from None because tool measures branches


def test_tool_does_not_measure_branches_stays_none():
    """PHP: tool doesn't measure branches (no file has branch data) → None"""
    test_lcov = """TN:
SF:src/handler.php
FN:1,handle
FNDA:1,handle
FNF:1
FNH:1
DA:1,1
DA:2,0
LF:2
LH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov, set())
    php_file = next(r for r in result if r["full_path"] == "src/handler.php")

    assert php_file["line_coverage"] == 50.0
    assert php_file["function_coverage"] == 100.0
    assert php_file["branch_coverage"] is None  # Tool doesn't measure branches


def test_tool_measures_all_metrics_empty_file_all_100():
    """Tool measures all metrics but file has 0 of each → all 100%"""
    test_lcov = """TN:
SF:src/empty.ts
LF:0
LH:0
FNF:0
FNH:0
BRF:0
BRH:0
end_of_record
SF:src/real.ts
FN:1,realFunc
FNDA:1,realFunc
FNF:1
FNH:1
DA:1,1
LF:1
LH:1
BRDA:1,0,0,1
BRF:1
BRH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov, set())
    empty_file = next(r for r in result if r["full_path"] == "src/empty.ts")

    assert empty_file["line_coverage"] == 100
    assert empty_file["function_coverage"] == 100
    assert empty_file["branch_coverage"] == 100


def test_parse_lcov_php_real_branches_none():
    """PHP (phpunit): tool doesn't measure branches → all files have branch_coverage=None"""
    with open("payloads/lcov/lcov-php-spiderplus.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["line_coverage"] == 15.1
    assert repo["function_coverage"] == 31.3
    assert repo["branch_coverage"] is None  # phpunit doesn't measure branches
    assert repo["branches_total"] == 0

    files = [r for r in result if r["level"] == "file"]
    assert all(f["branch_coverage"] is None for f in files)


def test_parse_lcov_jest_foxquilt_zero_branches_upgraded():
    """Jest (Foxquilt): tool measures branches → files with 0 branches get 100%"""
    with open("payloads/lcov/lcov-js-foxquilt.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content, set())

    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["branch_coverage"] == 69.0
    assert repo["branches_total"] > 0  # Jest measures branches

    files = [r for r in result if r["level"] == "file"]
    # No file should have None branch_coverage because Jest measures branches
    assert all(f["branch_coverage"] is not None for f in files)

    # Files with 0 branches_total should have branch_coverage=100 (nothing to cover)
    zero_branch_files = [f for f in files if f["branches_total"] == 0]
    assert len(zero_branch_files) > 0
    assert all(f["branch_coverage"] == 100 for f in zero_branch_files)

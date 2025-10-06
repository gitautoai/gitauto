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


def test_parse_lcov_dotnet_real():
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)

    assert len(result) > 0

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 22

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert repo_coverage["function_coverage"] == 13.95  # Real value from .NET LCOV
    assert repo_coverage["statement_coverage"] == 30.34  # Real value from .NET LCOV
    assert repo_coverage["line_coverage"] == 30.34  # Real value from .NET LCOV
    assert repo_coverage["branch_coverage"] == 4.17  # Real value from .NET LCOV


def test_fn_parsing_python():
    """Test FN parsing for Python 3-part format using real LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FN lines are parsed correctly (3-part format)
    # Example: FN:12,16,get_env_var
    assert "FN:12,16,get_env_var" in lcov_content
    assert "FN:9,10,test_owner" in lcov_content

    result = parse_lcov_coverage(lcov_content)
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

    result = parse_lcov_coverage(lcov_content)
    # Check that function coverage is calculated correctly
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 80.58


def test_fn_parsing_javascript():
    """Test FN parsing for JavaScript 2-part format using real LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    # Verify FN lines are parsed correctly (2-part format)
    # Example: FN:7,GlobalError
    assert "FN:7,GlobalError" in lcov_content
    assert "FN:30,RootLayout" in lcov_content

    result = parse_lcov_coverage(lcov_content)
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

    result = parse_lcov_coverage(lcov_content)
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

    result = parse_lcov_coverage(lcov_content)
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

    result = parse_lcov_coverage(lcov_content)
    # Check that function coverage is calculated correctly
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 13.95


def test_fn_fnda_parsing_formats():
    # Test all FN/FNDA formats: 2-part, 3-part, and with commas
    test_lcov = """TN:
SF:/test2part.js
FN:10,simpleFunction
FNDA:5,simpleFunction
FNF:1
FNH:1
DA:10,5
LH:1
LF:1
end_of_record
SF:/test3part.py
FN:20,25,pythonFunction
FNDA:3,pythonFunction
FNF:1
FNH:1
DA:20,3
LH:1
LF:1
end_of_record
SF:/testcommas.cs
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

    result = parse_lcov_coverage(test_lcov)

    # Should parse successfully
    assert len(result) > 0

    # Check repository level
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 75.0

    # Check that all formats parsed correctly
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 3

    # JavaScript file (2-part format)
    js_file = next(f for f in files if "test2part.js" in f["full_path"])
    assert js_file["function_coverage"] == 100.0

    # Python file (3-part format)
    py_file = next(f for f in files if "test3part.py" in f["full_path"])
    assert py_file["function_coverage"] == 100.0

    # C# file (commas in function names)
    cs_file = next(f for f in files if "testcommas.cs" in f["full_path"])
    assert cs_file["function_coverage"] == 50.0


def test_parse_lcov_gitauto_real_exact_counts():
    """Test parsing GitAuto repository LCOV file with exact file counts.

    This test verifies that the parser correctly filters out test files
    and produces the expected number of reports. It will fail if there's
    a bug in production causing incorrect file extraction.
    """
    with open("payloads/lcov/lcov-gitauto-20250922.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    result = parse_lcov_coverage(lcov_content)

    # Total reports should be: files + directories + repository
    # Expected: 282 files + 77 directories + 1 repository = 360 total
    assert len(result) == 360

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 282  # Non-test files only

    directory_level = [r for r in result if r["level"] == "directory"]
    assert len(directory_level) == 77  # Unique directories

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
        "conftest.py",  # pytest configuration file
        "services/webhook/utils/create_test_selection_comment.py",  # utility for test selection
        "utils/files/is_test_file.py",  # utility to detect test files
    ]

    for file_path in legitimate_files:
        file_found = next((f for f in file_level if f["full_path"] == file_path), None)
        assert (
            file_found is not None
        ), f"{file_path} should be included as a legitimate non-test file"



def test_malformed_fn_line_no_comma():
    """Test FN line without comma (line 58-59)"""
    test_lcov = """TN:
SF:/test.py
FN:10NoCommaHere
FNF:0
FNH:0
LF:0
LH:0
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 100.0


def test_malformed_fn_line_invalid_line_number():
    """Test FN line with invalid line number (line 88-90)"""
    test_lcov = """TN:
SF:/test.py
FN:notanumber,functionName
FNF:0
FNH:0
LF:0
LH:0
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 100.0


def test_malformed_fnda_line_no_comma():
    """Test FNDA line without comma (line 97-98)"""
    test_lcov = """TN:
SF:/test.py
FNDA:5NoCommaHere
FNF:0
FNH:0
LF:0
LH:0
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 100.0


def test_malformed_fnda_line_invalid_execution_count():
    """Test FNDA line with invalid execution count (line 103-104)"""
    test_lcov = """TN:
SF:/test.py
FNDA:notanumber,functionName
FNF:0
FNH:0
LF:0
LH:0
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 100.0


def test_brda_jump_to_function_exit():
    """Test BRDA with 'jump to the function exit' (line 131-133)"""
    test_lcov = """TN:
SF:/test.py
BRDA:10,0,jump to the function exit,0
BRF:1
BRH:0
LF:1
LH:1
DA:10,1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert "function exit" in files[0]["uncovered_branches"]


def test_brda_exit_the_module():
    """Test BRDA with 'exit the module' (line 142-144)"""
    test_lcov = """TN:
SF:/test.py
BRDA:20,0,exit the module,0
BRF:1
BRH:0
LF:1
LH:1
DA:20,1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert "module exit" in files[0]["uncovered_branches"]


def test_malformed_brda_line():
    """Test malformed BRDA line (line 158-160)"""
    test_lcov = """TN:
SF:/test.py
BRDA:invalid,data,here
BRF:0
BRH:0
LF:1
LH:1
DA:10,1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["branch_coverage"] == 100.0


def test_end_of_record_without_current_file():
    """Test end_of_record when current_file is None (line 186-187)"""
    test_lcov = """TN:
SF:tests/test_file.py
FN:10,testFunction
FNDA:1,testFunction
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    # Should skip test files and handle extra end_of_record
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 0  # Test file should be skipped


def test_end_of_record_with_empty_stats():
    """Test end_of_record when current_stats is empty (line 188-189)"""
    test_lcov = """TN:
SF:/test.py
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    # Should handle file with no stats
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    # File with no stats should still be included
    assert len(files) == 1


def test_skip_test_files_with_test_prefix():
    """Test skipping files with test_ prefix"""
    test_lcov = """TN:
SF:/test_something.py
FN:10,testFunction
FNDA:1,testFunction
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 0  # Test file should be skipped


def test_skip_test_files_with_test_suffix():
    """Test skipping files with _test.py suffix"""
    test_lcov = """TN:
SF:/something_test.py
FN:10,testFunction
FNDA:1,testFunction
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 0  # Test file should be skipped


def test_skip_test_files_in_tests_directory():
    """Test skipping files in tests directory"""
    test_lcov = """TN:
SF:/tests/something.py
FN:10,testFunction
FNDA:1,testFunction
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 0  # Test file should be skipped


def test_brda_with_dash_taken():
    """Test BRDA with dash as taken value"""
    test_lcov = """TN:
SF:/test.py
BRDA:10,0,0,-
BRF:1
BRH:0
LF:1
LH:1
DA:10,1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert files[0]["branch_coverage"] == 0.0


def test_empty_lcov_content():
    """Test with empty LCOV content"""
    test_lcov = ""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) == 1  # Only repository level
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["full_path"] == "All"
    assert repo["line_coverage"] == 100.0


def test_complex_branch_scenarios():
    """Test complex branch scenarios with multiple branch types"""
    test_lcov = """TN:
SF:/test.py

def test_malformed_fn_line_no_comma():
    """Test FN line without comma (line 58-59)"""
    test_lcov = """TN:
SF:/test.py
FN:10NoCommaHere
FNF:0
FNH:0
DA:10,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


def test_malformed_fn_line_invalid_line_number():
    """Test FN line with invalid line number (line 88-90)"""
    test_lcov = """TN:
SF:/test.py
FN:notanumber,functionName
FNF:0
FNH:0
DA:10,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


def test_malformed_fnda_line_no_comma():
    """Test FNDA line without comma (line 97-98)"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:5NoCommaHere
FNF:1
FNH:0
DA:10,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


def test_malformed_fnda_line_invalid_execution_count():
    """Test FNDA line with invalid execution count (line 103-104)"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:notanumber,testFunc
FNF:1
FNH:0
DA:10,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


def test_brda_jump_to_function_exit():
    """Test BRDA with 'jump to the function exit' (line 131-133)"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
BRDA:15,0,jump to the function exit,0
BRF:1
BRH:0
DA:10,1
DA:15,1
LH:2
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    file_report = files[0]
    assert "function exit" in file_report["uncovered_branches"]


def test_brda_exit_the_module():
    """Test BRDA with 'exit the module' (line 142-144)"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
BRDA:20,0,exit the module,0
BRF:1
BRH:0
DA:10,1
DA:20,1
LH:2
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    file_report = files[0]
    assert "module exit" in file_report["uncovered_branches"]


def test_malformed_brda_line():
    """Test malformed BRDA line (line 158-160)"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
BRDA:invalid,data,here
BRF:0
BRH:0
DA:10,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


def test_end_of_record_without_current_file():
    """Test end_of_record when current_file is None (line 186-187)"""
    test_lcov = """TN:
SF:/tests/test_file.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
DA:10,1
LH:1
LF:1
end_of_record
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    # Should skip test files and handle extra end_of_record
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo is not None


def test_end_of_record_without_current_stats():
    """Test end_of_record when current_stats is empty (line 188-189)"""
    test_lcov = """TN:
SF:/test.py
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    # Should handle empty stats gracefully
    assert len(result) > 0
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo is not None


def test_skip_test_files_with_test_prefix():
    """Test that files starting with test_ are skipped"""
    test_lcov = """TN:
SF:/test_something.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
DA:10,1
LH:1
LF:1
end_of_record
SF:/normal_file.py
FN:20,normalFunc
FNDA:1,normalFunc
FNF:1
FNH:1
DA:20,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert "normal_file.py" in files[0]["full_path"]


def test_skip_test_files_with_test_suffix():
    """Test that files ending with _test.py are skipped"""
    test_lcov = """TN:
SF:/something_test.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
DA:10,1
LH:1
LF:1
end_of_record
SF:/normal_file.py
FN:20,normalFunc
FNDA:1,normalFunc
FNF:1
FNH:1
DA:20,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert "normal_file.py" in files[0]["full_path"]


def test_skip_test_files_in_tests_directory():
    """Test that files in tests directory are skipped"""
    test_lcov = """TN:
SF:/tests/something.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
DA:10,1
LH:1
LF:1
end_of_record
SF:/src/normal_file.py
FN:20,normalFunc
FNDA:1,normalFunc
FNF:1
FNH:1
DA:20,1
LH:1
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert "normal_file.py" in files[0]["full_path"]


def test_brda_return_from_function():
    """Test BRDA with 'return from function' format"""
    test_lcov = """TN:
SF:/test.py
FN:10,testFunc
FNDA:1,testFunc
FNF:1
FNH:1
BRDA:15,0,return from function 'testFunc',1
BRF:1
BRH:1
DA:10,1
DA:15,1
LH:2
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    file_report = files[0]
    assert file_report["branch_coverage"] == 100.0


def test_empty_lcov_content():
    """Test with empty LCOV content"""
    test_lcov = ""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) == 1
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["full_path"] == "All"
    assert repo["line_coverage"] == 100.0


def test_directory_aggregation():
    """Test that directory stats are properly aggregated"""
    test_lcov = """TN:
SF:/src/module/file1.py
FN:10,func1
FNDA:1,func1
FNF:1
FNH:1
DA:10,1
LH:1
LF:1
end_of_record
SF:/src/module/file2.py
FN:20,func2
FNDA:0,func2
FNF:1

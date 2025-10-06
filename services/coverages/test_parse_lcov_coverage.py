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
    assert repo_coverage["function_coverage"] == 13.95
    assert repo_coverage["statement_coverage"] == 30.34
    assert repo_coverage["line_coverage"] == 30.34
    assert repo_coverage["branch_coverage"] == 4.17


def test_fn_parsing_python():
    """Test FN parsing for Python 3-part format using real LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert "FN:12,16,get_env_var" in lcov_content
    assert "FN:9,10,test_owner" in lcov_content

    result = parse_lcov_coverage(lcov_content)
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_python():
    """Test FNDA parsing for Python using real LCOV file"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert "FNDA:1,get_env_var" in lcov_content

    result = parse_lcov_coverage(lcov_content)
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 80.58


def test_fn_parsing_javascript():
    """Test FN parsing for JavaScript 2-part format using real LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert "FN:7,GlobalError" in lcov_content
    assert "FN:30,RootLayout" in lcov_content

    result = parse_lcov_coverage(lcov_content)
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_javascript():
    """Test FNDA parsing for JavaScript using real LCOV file"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert "FNDA:0,GlobalError" in lcov_content

    result = parse_lcov_coverage(lcov_content)
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 2.7


def test_fn_parsing_dotnet():
    """Test FN parsing for .NET with commas in function signatures using real LCOV file"""
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert (
        "FN:24,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)"
        in lcov_content
    )
    assert (
        "FN:53,.ctor(Salida.Models.MicrosipContext,Microsip.Core.IParameter)"
        in lcov_content
    )

    result = parse_lcov_coverage(lcov_content)
    assert len(result) > 0
    assert any(
        r["level"] == "file" and r["function_coverage"] is not None for r in result
    )


def test_fnda_parsing_dotnet():
    """Test FNDA parsing for .NET with commas in function signatures using real LCOV file"""
    with open("payloads/lcov/lcov-dotnet-real.info", "r", encoding=UTF8) as f:
        lcov_content = f.read()

    assert (
        "FNDA:0,.ctor(Microsoft.Extensions.Configuration.IConfiguration,System.String)"
        in lcov_content
    )
    assert (
        "FNDA:13,.ctor(Salida.Models.MicrosipContext,Microsip.Core.IParameter)"
        in lcov_content
    )

    result = parse_lcov_coverage(lcov_content)
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 13.95


def test_fn_fnda_parsing_formats():
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

    assert len(result) > 0

    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["function_coverage"] == 75.0

    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 3

    js_file = next(f for f in files if "test2part.js" in f["full_path"])
    assert js_file["function_coverage"] == 100.0

    py_file = next(f for f in files if "test3part.py" in f["full_path"])
    assert py_file["function_coverage"] == 100.0

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

    assert len(result) == 360

    repo_level = [r for r in result if r["level"] == "repository"]
    assert len(repo_level) == 1

    file_level = [r for r in result if r["level"] == "file"]
    assert len(file_level) == 282

    directory_level = [r for r in result if r["level"] == "directory"]
    assert len(directory_level) == 77

    repo_coverage = repo_level[0]
    assert repo_coverage["full_path"] == "All"
    assert isinstance(repo_coverage["statement_coverage"], float)
    assert isinstance(repo_coverage["line_coverage"], float)

    config_file = next((f for f in file_level if f["full_path"] == "config.py"), None)
    assert config_file is not None, "config.py should be included as a non-test file"

    legitimate_files = [
        "conftest.py",
        "services/webhook/utils/create_test_selection_comment.py",
        "utils/files/is_test_file.py",
    ]

    for file_path in legitimate_files:
        file_found = next((f for f in file_level if f["full_path"] == file_path), None)
        assert (
            file_found is not None
        ), f"{file_path} should be included as a legitimate non-test file"


def test_brda_parsing_function_exit():
    """Test BRDA parsing for 'jump to the function exit' branch description"""
    test_lcov = """TN:
SF:/test_func_exit.py
BRDA:10,0,jump to the function exit,5
BRDA:20,0,jump to the function exit,0
BRF:2
BRH:1
DA:10,5
DA:20,0
LH:1
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert files[0]["branch_coverage"] == 50.0
    assert "line 20, block 0, function exit" in files[0]["uncovered_branches"]


def test_brda_parsing_module_exit():
    """Test BRDA parsing for 'exit the module' branch description"""
    test_lcov = """TN:
SF:/test_module_exit.py
BRDA:15,0,exit the module,3
BRDA:25,0,exit the module,0
BRF:2
BRH:1
DA:15,3
DA:25,0
LH:1
LF:2
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1
    assert files[0]["branch_coverage"] == 50.0
    assert "line 25, block 0, module exit" in files[0]["uncovered_branches"]


def test_empty_file_handling():
    """Test handling of empty file (no current_file or no current_stats at end_of_record)"""
    test_lcov = """TN:
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) >= 1


def test_malformed_fn_line_no_comma():
    """Test FN line without comma"""
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
    """Test FN line with invalid line number"""
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
    """Test FNDA line without comma"""
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
    """Test FNDA line with invalid execution count"""
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
    """Test BRDA with 'jump to the function exit'"""
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
    """Test BRDA with 'exit the module'"""
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
    """Test malformed BRDA line"""
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
    """Test end_of_record when current_file is None"""
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
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 0


def test_end_of_record_with_empty_stats():
    """Test end_of_record when current_stats is empty"""
    test_lcov = """TN:
SF:/test.py
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0
    files = [r for r in result if r["level"] == "file"]
    assert len(files) == 1


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
    assert len(result) == 1
    repo = [r for r in result if r["level"] == "repository"][0]
    assert repo["full_path"] == "All"
    assert repo["line_coverage"] == 100.0


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
FNH:0
DA:20,0
LH:0
LF:1
end_of_record"""

    result = parse_lcov_coverage(test_lcov)
    assert len(result) > 0

    directory_level = [r for r in result if r["level"] == "directory"]
    assert len(directory_level) > 0

    src_module_dir = next(
        (d for d in directory_level if d["full_path"] == "/src/module"), None
    )
    assert src_module_dir is not None
    assert src_module_dir["function_coverage"] == 50.0

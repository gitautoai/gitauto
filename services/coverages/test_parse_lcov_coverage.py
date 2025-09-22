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

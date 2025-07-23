from services.coverages.create_coverage_report import create_coverage_report


def test_create_coverage_report_directory_level_empty_path():
    """Test directory level with empty path - covers lines 3, 4"""
    stats = {
        "lines_total": 100,
        "lines_covered": 80,
        "functions_total": 10,
        "functions_covered": 8,
        "branches_total": 20,
        "branches_covered": 15,
        "uncovered_lines": {1, 2, 3},
        "uncovered_functions": {(10, "test_func"), (20, 30, "another_func")},
        "uncovered_branches": {"branch1", "branch2"},
    }

    result = create_coverage_report("", stats, "directory")

    assert result["full_path"] == "."
    assert result["level"] == "directory"
    assert result["line_coverage"] == 80.0
    assert result["statement_coverage"] == 80.0
    assert result["function_coverage"] == 80.0
    assert result["branch_coverage"] == 75.0
    assert result["package_name"] is None
    assert result["uncovered_lines"] == ""  # Not file level
    assert result["uncovered_functions"] == "L10:test_func, L20-30:another_func"
    assert result["uncovered_branches"] == "branch1, branch2"


def test_create_coverage_report_directory_level_non_empty_path():
    """Test directory level with non-empty path - covers branch where condition is false"""
    stats = {
        "lines_total": 50,
        "lines_covered": 25,
        "functions_total": 5,
        "functions_covered": 3,
        "branches_total": 10,
        "branches_covered": 7,
        "uncovered_lines": {5, 10},
        "uncovered_functions": {(15, "func1")},
        "uncovered_branches": {"branch3"},
    }

    result = create_coverage_report("src/utils", stats, "directory")

    assert result["full_path"] == "src/utils"
    assert result["level"] == "directory"
    assert result["line_coverage"] == 50.0
    assert result["statement_coverage"] == 50.0
    assert result["function_coverage"] == 60.0
    assert result["branch_coverage"] == 70.0


def test_create_coverage_report_file_level_with_coverage():
    """Test file level with coverage > 0 - covers lines 6, 14, 22, 31 and uncovered_lines logic"""
    stats = {
        "lines_total": 200,
        "lines_covered": 150,
        "functions_total": 20,
        "functions_covered": 15,
        "branches_total": 40,
        "branches_covered": 30,
        "uncovered_lines": {5, 10, 15, 20},
        "uncovered_functions": {(25, "test_method"), (35, 45, "complex_func")},
        "uncovered_branches": {"branch4", "branch5"},
    }

    result = create_coverage_report("src/main.py", stats, "file")

    assert result["full_path"] == "src/main.py"
    assert result["level"] == "file"
    assert result["line_coverage"] == 75.0
    assert result["statement_coverage"] == 75.0
    assert result["function_coverage"] == 75.0
    assert result["branch_coverage"] == 75.0
    assert result["uncovered_lines"] == "5, 10, 15, 20"  # File level with coverage > 0
    assert result["uncovered_functions"] == "L25:test_method, L35-45:complex_func"
    assert result["uncovered_branches"] == "branch4, branch5"


def test_create_coverage_report_file_level_zero_coverage():
    """Test file level with zero coverage"""
    stats = {
        "lines_total": 100,
        "lines_covered": 0,
        "functions_total": 10,
        "functions_covered": 0,
        "branches_total": 20,
        "branches_covered": 0,
        "uncovered_lines": {1, 2, 3, 4, 5},
        "uncovered_functions": {(10, "func1"), (20, 30, "func2")},
        "uncovered_branches": {"branch1", "branch2"},
    }

    result = create_coverage_report("src/unused.py", stats, "file")

    assert result["full_path"] == "src/unused.py"
    assert result["level"] == "file"
    assert result["line_coverage"] == 0.0
    assert result["statement_coverage"] == 0.0
    assert result["function_coverage"] == 0.0
    assert result["branch_coverage"] == 0.0
    assert result["uncovered_lines"] == ""  # Zero coverage means empty string
    assert result["uncovered_functions"] == "L10:func1, L20-30:func2"
    assert result["uncovered_branches"] == "branch1, branch2"


def test_create_coverage_report_repository_level():
    """Test repository level"""
    stats = {
        "lines_total": 1000,
        "lines_covered": 850,
        "functions_total": 100,
        "functions_covered": 90,
        "branches_total": 200,
        "branches_covered": 180,
        "uncovered_lines": set(range(1, 151)),  # 150 uncovered lines
        "uncovered_functions": {(i, f"func_{i}") for i in range(1, 11)},  # 10 functions
        "uncovered_branches": {f"branch_{i}" for i in range(1, 21)},  # 20 branches
    }

    result = create_coverage_report("All", stats, "repository")

    assert result["full_path"] == "All"
    assert result["level"] == "repository"
    assert result["line_coverage"] == 85.0
    assert result["statement_coverage"] == 85.0
    assert result["function_coverage"] == 90.0
    assert result["branch_coverage"] == 90.0
    assert result["uncovered_lines"] == ""  # Not file level
    assert "L1:func_1" in result["uncovered_functions"]
    assert "L10:func_10" in result["uncovered_functions"]
    assert "branch_1" in result["uncovered_branches"]
    assert "branch_20" in result["uncovered_branches"]


def test_create_coverage_report_zero_totals():
    """Test edge case with zero totals - should default to 100% coverage"""
    stats = {
        "lines_total": 0,
        "lines_covered": 0,
        "functions_total": 0,
        "functions_covered": 0,
        "branches_total": 0,
        "branches_covered": 0,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
    }

    result = create_coverage_report("empty.py", stats, "file")

    assert result["full_path"] == "empty.py"
    assert result["level"] == "file"
    assert result["line_coverage"] == 100.0
    assert result["statement_coverage"] == 100.0
    assert result["function_coverage"] == 100.0
    assert result["branch_coverage"] == 100.0
    assert result["uncovered_lines"] == ""
    assert result["uncovered_functions"] == ""
    assert result["uncovered_branches"] == ""


def test_create_coverage_report_mixed_function_formats():
    """Test with mixed function formats (2-tuple and 3-tuple)"""
    stats = {
        "lines_total": 100,
        "lines_covered": 80,
        "functions_total": 5,
        "functions_covered": 3,
        "branches_total": 10,
        "branches_covered": 8,
        "uncovered_lines": {1, 2},
        "uncovered_functions": {
            (10, "simple_func"),  # 2-tuple format
            (20, 30, "complex_func"),  # 3-tuple format
            (40, "another_simple"),  # 2-tuple format
            (50, 60, "another_complex"),  # 3-tuple format
        },
        "uncovered_branches": {"branch1", "branch2"},
    }

    result = create_coverage_report("test.py", stats, "file")

    # Check that both formats are handled correctly
    uncovered_funcs = result["uncovered_functions"]
    assert "L10:simple_func" in uncovered_funcs
    assert "L20-30:complex_func" in uncovered_funcs
    assert "L40:another_simple" in uncovered_funcs
    assert "L50-60:another_complex" in uncovered_funcs


def test_create_coverage_report_empty_uncovered_sets():
    """Test with empty uncovered sets"""
    stats = {
        "lines_total": 100,
        "lines_covered": 100,
        "functions_total": 10,
        "functions_covered": 10,
        "branches_total": 20,
        "branches_covered": 20,
        "uncovered_lines": set(),
        "uncovered_functions": set(),
        "uncovered_branches": set(),
    }

    result = create_coverage_report("perfect.py", stats, "file")

    assert result["line_coverage"] == 100.0
    assert result["function_coverage"] == 100.0
    assert result["branch_coverage"] == 100.0
    assert result["uncovered_lines"] == ""
    assert result["uncovered_functions"] == ""
    assert result["uncovered_branches"] == ""


def test_create_coverage_report_rounding():
    """Test coverage percentage rounding"""
    stats = {
        "lines_total": 3,
        "lines_covered": 1,  # 33.333...%
        "functions_total": 3,
        "functions_covered": 2,  # 66.666...%
        "branches_total": 7,
        "branches_covered": 5,  # 71.428...%
        "uncovered_lines": {2, 3},
        "uncovered_functions": {(10, "func1")},
        "uncovered_branches": {"branch1", "branch2"},
    }

    result = create_coverage_report("rounding.py", stats, "file")

    assert result["line_coverage"] == 33.33
    assert result["statement_coverage"] == 33.33
    assert result["function_coverage"] == 66.67
    assert result["branch_coverage"] == 71.43


def test_create_coverage_report_non_file_level_uncovered_lines():
    """Test that uncovered_lines is empty for non-file levels"""
    stats = {
        "lines_total": 100,
        "lines_covered": 80,
        "functions_total": 10,
        "functions_covered": 8,
        "branches_total": 20,
        "branches_covered": 15,
        "uncovered_lines": {1, 2, 3, 4, 5},
        "uncovered_functions": {(10, "func1")},
        "uncovered_branches": {"branch1"},
    }

    # Test directory level
    result_dir = create_coverage_report("src", stats, "directory")
    assert result_dir["uncovered_lines"] == ""

    # Test repository level
    result_repo = create_coverage_report("All", stats, "repository")
    assert result_repo["uncovered_lines"] == ""


def test_create_coverage_report_other_level():
    """Test with a level that's not 'directory' to ensure the if condition works correctly"""
    stats = {
        "lines_total": 50,
        "lines_covered": 40,
        "functions_total": 5,
        "functions_covered": 4,
        "branches_total": 10,
        "branches_covered": 8,
        "uncovered_lines": {1, 2},
        "uncovered_functions": {(10, "func1")},
        "uncovered_branches": {"branch1"},
    }

    result = create_coverage_report("", stats, "file")

    # Path should remain empty since level is not "directory"
    assert result["full_path"] == ""
    assert result["level"] == "file"

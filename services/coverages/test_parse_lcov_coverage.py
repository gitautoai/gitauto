import os
import pytest
from unittest.mock import patch, MagicMock

from services.coverages.parse_lcov_coverage import parse_lcov_coverage
from services.coverages.create_empty_stats import create_empty_stats


@pytest.fixture
def mock_create_coverage_report():
    """Mock the create_coverage_report function to return a simple dictionary."""
    with patch('services.coverages.parse_lcov_coverage.create_coverage_report') as mock:
        mock.side_effect = lambda path, stats, level: {
            'full_path': path,
            'level': level,
            'stats': stats
        }
        yield mock


def test_parse_lcov_coverage_empty_content():
    """Test parsing empty LCOV content."""
    result = parse_lcov_coverage("")
    
    # Should return only a repository report with empty stats
    assert len(result) == 1
    assert result[0]['level'] == 'repository'
    assert result[0]['full_path'] == 'All'
    assert result[0]['line_coverage'] == 100  # Default when no lines


def test_parse_lcov_coverage_basic_file():
    """Test parsing basic file coverage data."""
    lcov_content = """SF:src/example.py
FN:10,example_function
FNDA:1,example_function
FNF:1
FNH:1
DA:10,1
DA:11,1
DA:12,0
LF:3
LH:2
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    assert len(result) == 3  # file, directory, and repository reports
    
    # Check file report
    file_report = next(r for r in result if r['level'] == 'file')
    assert file_report['full_path'] == 'src/example.py'
    
    # Check directory report
    dir_report = next(r for r in result if r['level'] == 'directory')
    assert dir_report['full_path'] == 'src'
    
    # Check repository report
    repo_report = next(r for r in result if r['level'] == 'repository')
    assert repo_report['full_path'] == 'All'


def test_parse_lcov_coverage_skip_test_files():
    """Test that test files are skipped."""
    lcov_content = """SF:src/tests/test_example.py
FN:10,test_function
FNDA:1,test_function
FNF:1
FNH:1
DA:10,1
DA:11,1
LF:2
LH:2
end_of_record
SF:src/test_file.py
FN:5,another_test
FNDA:1,another_test
FNF:1
FNH:1
DA:5,1
LF:1
LH:1
end_of_record
SF:src/file_test.py
FN:15,test_method
FNDA:1,test_method
FNF:1
FNH:1
DA:15,1
LF:1
LH:1
end_of_record
SF:src/actual.py
FN:20,real_function
FNDA:1,real_function
FNF:1
FNH:1
DA:20,1
LF:1
LH:1
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    # Only one file should be processed (src/actual.py)
    file_reports = [r for r in result if r['level'] == 'file']
    assert len(file_reports) == 1
    assert file_reports[0]['full_path'] == 'src/actual.py'


def test_parse_lcov_coverage_function_formats():
    """Test parsing different function formats."""
    lcov_content = """SF:src/functions.py
FN:10,20,python_function
FN:30,js_function
FNDA:1,python_function
FNDA:0,js_function
FNF:2
FNH:1
DA:10,1
DA:30,0
LF:2
LH:1
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    file_report = next(r for r in result if r['level'] == 'file')
    
    # Check function coverage percentage (1 out of 2 functions covered = 50%)
    assert file_report['function_coverage'] == 50.0
    
    # Check uncovered functions string format
    uncovered_funcs_str = file_report['uncovered_functions']
    assert 'L30:js_function' in uncovered_funcs_str


def test_parse_lcov_coverage_branch_data():
    """Test parsing branch coverage data."""
    lcov_content = """SF:src/branches.py
FN:10,branch_function
FNDA:1,branch_function
BRDA:15,1,jump to line 20,1
BRDA:25,2,jump to the function exit,0
BRDA:30,3,return from function 'branch_function',1
BRDA:35,4,exit the module,0
BRDA:40,5,6,1
BRF:5
BRH:3
DA:10,1
DA:15,1
DA:25,1
DA:30,1
DA:35,1
DA:40,1
LF:6
LH:6
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    file_report = next(r for r in result if r['level'] == 'file')
    
    # Check branch coverage (3 out of 5 branches covered = 60%)
    assert file_report['branch_coverage'] == 60.0
    
    # Check uncovered branches string format
    uncovered_branches_str = file_report['uncovered_branches']
    assert 'function exit' in uncovered_branches_str
    assert 'module exit' in uncovered_branches_str


def test_parse_lcov_coverage_line_data():
    """Test parsing line coverage data."""
    lcov_content = """SF:src/lines.py
DA:10,1
DA:11,0
DA:12,1
DA:13,0
LF:4
LH:2
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    file_report = next(r for r in result if r['level'] == 'file')
    
    # Check line coverage (2 out of 4 lines covered = 50%)
    assert file_report['line_coverage'] == 50.0
    
    # Check uncovered lines - should be empty for file level when coverage > 0
    # (based on create_coverage_report logic)
    uncovered_lines_str = file_report['uncovered_lines']
    assert uncovered_lines_str == ""


def test_parse_lcov_coverage_multiple_files():
    """Test parsing multiple files."""
    lcov_content = """SF:src/file1.py
FN:10,func1
FNDA:1,func1
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record
SF:src/file2.py
FN:20,func2
FNDA:0,func2
FNF:1
FNH:0
DA:20,0
LF:1
LH:0
end_of_record
SF:src/subdir/file3.py
FN:30,func3
FNDA:1,func3
FNF:1
FNH:1
DA:30,1
LF:1
LH:1
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    # Should have 6 reports: 3 files, 2 directories, 1 repository
    assert len(result) == 6
    
    # Check file reports
    file_reports = [r for r in result if r['level'] == 'file']
    assert len(file_reports) == 3
    file_paths = [r['full_path'] for r in file_reports]
    assert 'src/file1.py' in file_paths
    assert 'src/file2.py' in file_paths
    assert 'src/subdir/file3.py' in file_paths
    
    # Check directory reports
    dir_reports = [r for r in result if r['level'] == 'directory']
    assert len(dir_reports) == 2
    dir_paths = [r['full_path'] for r in dir_reports]
    assert 'src' in dir_paths
    assert 'src/subdir' in dir_paths
    
    # Check repository report
    repo_reports = [r for r in result if r['level'] == 'repository']
    assert len(repo_reports) == 1
    assert repo_reports[0]['full_path'] == 'All'


def test_parse_lcov_coverage_malformed_lines():
    """Test handling of malformed lines."""
    lcov_content = """SF:src/malformed.py
FN:invalid_line
FNDA:not_a_number,func
BRDA:invalid_branch_data
DA:not_a_line,1
FN:10,20,30,too_many_parts
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record
"""
    # Should not raise exceptions for malformed lines
    result = parse_lcov_coverage(lcov_content)
    
    # Should still process valid lines
    assert len(result) == 3  # file, directory, and repository reports


@patch('services.coverages.parse_lcov_coverage.print')
def test_parse_lcov_coverage_branch_error_handling(mock_print):
    """Test error handling in branch data parsing."""
    lcov_content = """SF:src/error.py
BRDA:invalid,data,here,now
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    # Should log the error
    mock_print.assert_called_with("Error parsing line: BRDA:invalid,data,here,now")
    
    # Should still return reports
    assert len(result) == 3  # file, directory, and repository reports


def test_parse_lcov_coverage_with_exception():
    """Test the handle_exceptions decorator behavior."""
    with patch('services.coverages.parse_lcov_coverage.iter', side_effect=Exception("Test exception")):
        result = parse_lcov_coverage("SF:src/file.py")
        
        # Should return the default value from the decorator
        assert result == []


def test_parse_lcov_coverage_empty_records():
    """Test handling of empty records."""
    lcov_content = """SF:src/empty.py
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    # Should still create reports
    assert len(result) == 3  # file, directory, and repository reports


def test_parse_lcov_coverage_with_mock_create_coverage_report(mock_create_coverage_report):
    """Test interaction with create_coverage_report."""
    lcov_content = """SF:src/example.py
FN:10,example_function
FNDA:1,example_function
DA:10,1
end_of_record
"""
    result = parse_lcov_coverage(lcov_content)
    
    # Check that create_coverage_report was called with correct arguments
    assert mock_create_coverage_report.call_count == 3
    
    # Check file call
    file_call = next(call for call in mock_create_coverage_report.call_args_list 
                    if call[0][0] == 'src/example.py')
    assert file_call[0][2] == 'file'
    
    # Check directory call
    dir_call = next(call for call in mock_create_coverage_report.call_args_list 
                   if call[0][0] == 'src')
    assert dir_call[0][2] == 'directory'
    
    # Check repository call
    repo_call = next(call for call in mock_create_coverage_report.call_args_list 
                    if call[0][0] == 'All')
    assert repo_call[0][2] == 'repository'
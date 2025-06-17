import json
import subprocess
from unittest.mock import Mock, patch

from services.github.repositories.get_repository_stats import (
    DEFAULT_REPO_STATS,
    get_repository_stats,
)


def test_get_repository_stats_success():
    mock_result = Mock()
    mock_result.stdout = """{
        "header": {
            "n_files": 10
        },
        "SUM": {
            "blank": 50,
            "comment": 30,
            "code": 200
        }
    }"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 10,
        "blank_lines": 50,
        "comment_lines": 30,
        "code_lines": 200,
    }


def test_get_repository_stats_with_extra_text_before_json():
    mock_result = Mock()
    mock_result.stdout = """Some extra text before JSON
{
    "header": {
        "n_files": 5
    },
    "SUM": {
        "blank": 25,
        "comment": 15,
        "code": 100
    }
}"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 5,
        "blank_lines": 25,
        "comment_lines": 15,
        "code_lines": 100,
    }


def test_get_repository_stats_with_extra_text_after_json():
    mock_result = Mock()
    mock_result.stdout = """{
    "header": {
        "n_files": 3
    },
    "SUM": {
        "blank": 10,
        "comment": 5,
        "code": 50
    }
}
Some extra text after JSON"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 3,
        "blank_lines": 10,
        "comment_lines": 5,
        "code_lines": 50,
    }


def test_get_repository_stats_with_extra_text_before_and_after_json():
    mock_result = Mock()
    mock_result.stdout = """Extra text before
{
    "header": {
        "n_files": 7
    },
    "SUM": {
        "blank": 35,
        "comment": 20,
        "code": 150
    }
}
Extra text after"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 7,
        "blank_lines": 35,
        "comment_lines": 20,
        "code_lines": 150,
    }


def test_get_repository_stats_invalid_json_format():
    mock_result = Mock()
    mock_result.stdout = "No JSON braces here"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_malformed_json():
    mock_result = Mock()
    mock_result.stdout = "{ invalid json }"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_missing_header():
    mock_result = Mock()
    mock_result.stdout = """{
        "SUM": {
            "blank": 25,
            "comment": 15,
            "code": 100
        }
    }"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 0,
        "blank_lines": 25,
        "comment_lines": 15,
        "code_lines": 100,
    }


def test_get_repository_stats_missing_sum():
    mock_result = Mock()
    mock_result.stdout = """{
        "header": {
            "n_files": 5
        }
    }"""
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == {
        "file_count": 5,
        "blank_lines": 0,
        "comment_lines": 0,
        "code_lines": 0,
    }


def test_get_repository_stats_empty_json():
    mock_result = Mock()
    mock_result.stdout = "{}"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_subprocess_error():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cloc")):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_only_closing_brace():
    mock_result = Mock()
    mock_result.stdout = "}"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_only_opening_brace():
    mock_result = Mock()
    mock_result.stdout = "{"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS


def test_get_repository_stats_braces_in_wrong_order():
    mock_result = Mock()
    mock_result.stdout = "}{"
    
    with patch("subprocess.run", return_value=mock_result):
        result = get_repository_stats("/test/path")
    
    assert result == DEFAULT_REPO_STATS

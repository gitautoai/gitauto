from unittest.mock import patch, Mock
import pytest
from requests.exceptions import RequestException

from services.github.pulls.get_pull_request_files import get_pull_request_files
from config import PER_PAGE


@pytest.fixture
def mock_response():
    def _create_mock_response(status_code=200, json_data=None):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = json_data if json_data is not None else []
        return mock
    return _create_mock_response


def test_get_pull_request_files_success(mock_response):
    test_files = [
        {"filename": "test1.py", "status": "added"},
        {"filename": "test2.py", "status": "modified"},
    ]
    
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(json_data=test_files)
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert result == [
            {"filename": "test1.py", "status": "added"},
            {"filename": "test2.py", "status": "modified"},
        ]
        mock_get.assert_called_once()


def test_get_pull_request_files_pagination(mock_response):
    page1_files = [{"filename": f"file{i}.py", "status": "added"} for i in range(PER_PAGE)]
    page2_files = [{"filename": "lastfile.py", "status": "modified"}]
    
    with patch("requests.get") as mock_get:
        mock_get.side_effect = [
            mock_response(json_data=page1_files),
            mock_response(json_data=page2_files),
            mock_response(json_data=[])
        ]
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert len(result) == len(page1_files) + len(page2_files)
        assert result[-1] == {"filename": "lastfile.py", "status": "modified"}
        assert mock_get.call_count == 3


def test_get_pull_request_files_empty_response(mock_response):
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(json_data=[])
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert result == []
        mock_get.assert_called_once()


def test_get_pull_request_files_invalid_data(mock_response):
    invalid_files = [
        {"invalid_key": "value"},
        {"filename": "test.py"},  # Missing status
        {"status": "added"},      # Missing filename
        {"filename": "valid.py", "status": "modified"},  # This one is valid
    ]
    
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_response(json_data=invalid_files)
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert len(result) == 1
        assert result[0] == {"filename": "valid.py", "status": "modified"}
        mock_get.assert_called_once()


def test_get_pull_request_files_request_error(mock_response):
    with patch("requests.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert result == []
        mock_get.assert_called_once()


def test_get_pull_request_files_http_error(mock_response):
    error_response = mock_response(status_code=404)
    error_response.raise_for_status = Mock(side_effect=RequestException("404 Client Error"))
    
    with patch("requests.get") as mock_get:
        mock_get.return_value = error_response
        
        result = get_pull_request_files(
            url="https://api.github.com/repos/test/test/pulls/1/files",
            token="test_token"
        )
        
        assert result == []
        mock_get.assert_called_once()
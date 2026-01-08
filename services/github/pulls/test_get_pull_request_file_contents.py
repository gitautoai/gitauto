from unittest.mock import patch, Mock
import pytest
from services.github.pulls.get_pull_request_file_contents import (
    get_pull_request_file_contents,
)


@pytest.fixture
def mock_requests():
    with patch("services.github.pulls.get_pull_request_file_contents.requests") as mock:
        yield mock


@pytest.fixture
def mock_create_headers():
    with patch(
        "services.github.pulls.get_pull_request_file_contents.create_headers"
    ) as mock:
        mock.return_value = {"Authorization": "token test_token"}
        yield mock


@pytest.fixture
def mock_get_remote_file_content():
    with patch(
        "services.github.pulls.get_pull_request_file_contents.get_remote_file_content"
    ) as mock:
        yield mock


def test_get_pull_request_file_contents_success(
    mock_requests,
    mock_create_headers,
    mock_get_remote_file_content,
    create_test_base_args,
):
    url = "https://api.github.com/repos/owner/repo/pulls/1/files"
    base_args = create_test_base_args(token="test_token")

    # Mock responses for pagination
    response1 = Mock()
    response1.json.return_value = [{"filename": "file1.py"}, {"filename": "file2.py"}]
    response2 = Mock()
    response2.json.return_value = []

    mock_requests.get.side_effect = [response1, response2]
    mock_get_remote_file_content.side_effect = ["content1", "content2"]

    # Act
    result = get_pull_request_file_contents(url, base_args)

    # Assert
    assert result == ["content1", "content2"]
    mock_create_headers.assert_called_once_with(token="test_token")
    assert mock_requests.get.call_count == 2
    mock_get_remote_file_content.assert_any_call(
        file_path="file1.py", base_args=base_args
    )
    mock_get_remote_file_content.assert_any_call(
        file_path="file2.py", base_args=base_args
    )


def test_get_pull_request_file_contents_empty(
    mock_requests,
    mock_create_headers,
    mock_get_remote_file_content,
    create_test_base_args,
):
    url = "https://api.github.com/repos/owner/repo/pulls/1/files"
    base_args = create_test_base_args(token="test_token")

    response = Mock()
    response.json.return_value = []
    mock_requests.get.return_value = response

    # Act
    result = get_pull_request_file_contents(url, base_args)

    # Assert
    assert not result
    mock_create_headers.assert_called_once_with(token="test_token")
    mock_requests.get.assert_called_once()
    mock_get_remote_file_content.assert_not_called()


def test_get_pull_request_file_contents_http_error(
    mock_requests, mock_create_headers, create_test_base_args
):
    url = "https://api.github.com/repos/owner/repo/pulls/1/files"
    base_args = create_test_base_args(token="test_token")

    mock_requests.get.side_effect = Exception("HTTP Error")

    # Act
    result = get_pull_request_file_contents(url, base_args)

    # Assert
    assert result is None
    mock_create_headers.assert_called_once_with(token="test_token")
    mock_requests.get.assert_called_once()

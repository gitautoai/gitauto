# pylint: disable=unused-argument,too-many-instance-attributes
from unittest.mock import patch, MagicMock

import pytest
import requests
from faker import Faker
from requests import HTTPError

from services.github.comments.delete_comment import delete_comment

fake = Faker()


@pytest.fixture
def mock_delete_response():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_delete_comment_success(mock_delete_response):
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        with patch(
            "services.github.comments.delete_comment.create_headers"
        ) as mock_headers:
            mock_delete.return_value = mock_delete_response
            mock_headers.return_value = {"Authorization": f"Bearer {token}"}

            result = delete_comment(
                owner=owner,
                repo=repo,
                token=token,
                comment_id=comment_id,
            )

            mock_delete.assert_called_once()
            mock_headers.assert_called_once_with(token=token)
            mock_delete_response.raise_for_status.assert_called_once()
            assert result is None


def test_delete_comment_with_different_comment_id(mock_delete_response):
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(
            owner=owner,
            repo=repo,
            token=token,
            comment_id=comment_id,
        )

        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert str(comment_id) in actual_call[1]["url"]


def test_delete_comment_http_error_handled():
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    mock_response = MagicMock()
    http_error = HTTPError("404 Not Found")
    mock_error_response = MagicMock()
    mock_error_response.status_code = 404
    mock_error_response.reason = "Not Found"
    mock_error_response.text = "Comment not found"
    http_error.response = mock_error_response
    mock_response.raise_for_status.side_effect = http_error

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_response

        result = delete_comment(
            owner=owner,
            repo=repo,
            token=token,
            comment_id=comment_id,
        )

        assert result is None
        mock_delete.assert_called_once()


def test_delete_comment_request_timeout_handled():
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.side_effect = requests.exceptions.Timeout("Request timed out")

        result = delete_comment(
            owner=owner,
            repo=repo,
            token=token,
            comment_id=comment_id,
        )

        assert result is None
        mock_delete.assert_called_once()


def test_delete_comment_uses_correct_timeout(mock_delete_response):
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        with patch("services.github.comments.delete_comment.TIMEOUT", 60):
            mock_delete.return_value = mock_delete_response

            delete_comment(
                owner=owner,
                repo=repo,
                token=token,
                comment_id=comment_id,
            )

            mock_delete.assert_called_once()
            actual_call = mock_delete.call_args
            assert actual_call[1]["timeout"] == 60


def test_delete_comment_uses_github_api_url(mock_delete_response):
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        with patch(
            "services.github.comments.delete_comment.GITHUB_API_URL",
            "https://custom.api.github.com",
        ):
            mock_delete.return_value = mock_delete_response

            delete_comment(
                owner=owner,
                repo=repo,
                token=token,
                comment_id=comment_id,
            )

            mock_delete.assert_called_once()
            actual_call = mock_delete.call_args
            assert "custom.api.github.com" in actual_call[1]["url"]


@pytest.mark.parametrize("comment_id", [1, 999999, 123456789])
def test_delete_comment_with_various_comment_ids(mock_delete_response, comment_id):
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.return_value = mock_delete_response

        delete_comment(
            owner=owner,
            repo=repo,
            token=token,
            comment_id=comment_id,
        )

        mock_delete.assert_called_once()
        actual_call = mock_delete.call_args
        assert str(comment_id) in actual_call[1]["url"]


def test_delete_comment_connection_error_handled():
    owner = fake.user_name()
    repo = fake.slug()
    token = fake.sha256()
    comment_id = fake.random_int(min=1000, max=99999)

    with patch("services.github.comments.delete_comment.delete") as mock_delete:
        mock_delete.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        result = delete_comment(
            owner=owner,
            repo=repo,
            token=token,
            comment_id=comment_id,
        )

        assert result is None
        mock_delete.assert_called_once()


def test_delete_comment_decorator_configuration():
    assert hasattr(delete_comment, "__wrapped__")

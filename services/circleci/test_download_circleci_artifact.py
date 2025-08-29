from unittest.mock import patch, MagicMock
from services.circleci.download_circleci_artifact import download_circleci_artifact


def test_download_circleci_artifact_success():
    mock_response = MagicMock()
    mock_response.content = b"test coverage content"
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.download_circleci_artifact.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = download_circleci_artifact(
            artifact_url="https://example.com/artifact.lcov", token="test-token"
        )

        assert result == "test coverage content"
        mock_get.assert_called_once_with(
            "https://example.com/artifact.lcov",
            headers={"Circle-Token": "test-token"},
            timeout=120,
        )


def test_download_circleci_artifact_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 404")

    with patch("services.circleci.download_circleci_artifact.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = download_circleci_artifact(
            artifact_url="https://example.com/nonexistent.lcov", token="test-token"
        )

        assert result == ""


def test_download_circleci_artifact_empty_content():
    mock_response = MagicMock()
    mock_response.content = b""
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.download_circleci_artifact.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = download_circleci_artifact(
            artifact_url="https://example.com/empty.lcov", token="test-token"
        )

        assert result == ""

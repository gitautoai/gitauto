from unittest.mock import patch, MagicMock
from services.circleci.get_job_artifacts import get_circleci_job_artifacts


def test_get_circleci_job_artifacts_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {"path": "coverage/lcov.info", "url": "https://example.com/lcov.info"},
            {"path": "test-results.xml", "url": "https://example.com/test-results.xml"},
        ],
        "next_page_token": None,
    }
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="123", circle_token="test-token"
        )

        assert len(result) == 2
        assert result[0]["path"] == "coverage/lcov.info"
        assert result[1]["path"] == "test-results.xml"

        mock_get.assert_called_once_with(
            url="https://circleci.com/api/v2/project/gh/owner/repo/job/123/artifacts",
            headers={"Circle-Token": "test-token"},
            timeout=120,
        )


def test_get_circleci_job_artifacts_empty_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status.return_value = None

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="456", circle_token="test-token"
        )

        assert result == []


def test_get_circleci_job_artifacts_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 404")

    with patch("services.circleci.get_job_artifacts.get") as mock_get:
        mock_get.return_value = mock_response

        result = get_circleci_job_artifacts(
            project_slug="gh/owner/repo", job_number="999", circle_token="test-token"
        )

        assert result == []

from unittest.mock import Mock, patch

from services.circleci.get_project_pipelines import get_project_pipelines


@patch("services.circleci.get_project_pipelines.requests.get")
def test_get_project_pipelines_success(mock_get):
    project_slug = "gh/owner/repo"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"id": "pipeline-1", "number": 1},
            {"id": "pipeline-2", "number": 2},
        ],
        "next_page_token": None,
    }
    mock_get.return_value = mock_response

    result = get_project_pipelines(project_slug, token)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "pipeline-1"
    mock_get.assert_called_once()


@patch("services.circleci.get_project_pipelines.requests.get")
def test_get_project_pipelines_with_branch(mock_get):
    project_slug = "gh/owner/repo"
    token = "test-token"
    branch = "main"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": [], "next_page_token": None}
    mock_get.return_value = mock_response

    get_project_pipelines(project_slug, token, branch=branch)

    call_url = mock_get.call_args[1]["url"]
    assert "branch=main" in call_url


@patch("services.circleci.get_project_pipelines.requests.get")
def test_get_project_pipelines_not_found(mock_get):
    project_slug = "gh/nonexistent/repo"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_project_pipelines(project_slug, token)

    assert result == []


@patch("services.circleci.get_project_pipelines.requests.get")
def test_get_project_pipelines_pagination(mock_get):
    project_slug = "gh/owner/repo"
    token = "test-token"

    page1 = Mock()
    page1.status_code = 200
    page1.json.return_value = {
        "items": [{"id": f"pipeline-{i}"} for i in range(20)],
        "next_page_token": "token123",
    }

    page2 = Mock()
    page2.status_code = 200
    page2.json.return_value = {
        "items": [{"id": "pipeline-20"}],
        "next_page_token": None,
    }

    mock_get.side_effect = [page1, page2]

    result = get_project_pipelines(project_slug, token, max_pages=2)

    assert len(result) == 21
    assert mock_get.call_count == 2


@patch("services.circleci.get_project_pipelines.requests.get")
def test_get_project_pipelines_http_error(mock_get):
    project_slug = "gh/owner/repo"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = RuntimeError("Server Error")
    mock_get.return_value = mock_response

    result = get_project_pipelines(project_slug, token)

    assert result == []

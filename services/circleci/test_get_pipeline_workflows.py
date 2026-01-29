from unittest.mock import Mock, patch

from services.circleci.get_pipeline_workflows import get_pipeline_workflows


@patch("services.circleci.get_pipeline_workflows.requests.get")
def test_get_pipeline_workflows_success(mock_get):
    pipeline_id = "test-pipeline-id"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {"id": "workflow-1", "name": "build", "status": "success"},
            {"id": "workflow-2", "name": "test", "status": "running"},
        ]
    }
    mock_get.return_value = mock_response

    result = get_pipeline_workflows(pipeline_id, token)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "workflow-1"
    mock_get.assert_called_once_with(
        url=f"https://circleci.com/api/v2/pipeline/{pipeline_id}/workflow",
        headers={"Circle-Token": token},
        timeout=120,
    )


@patch("services.circleci.get_pipeline_workflows.requests.get")
def test_get_pipeline_workflows_not_found(mock_get):
    pipeline_id = "nonexistent-pipeline"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_pipeline_workflows(pipeline_id, token)

    assert result == []


@patch("services.circleci.get_pipeline_workflows.requests.get")
def test_get_pipeline_workflows_empty_items(mock_get):
    pipeline_id = "test-pipeline-id"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_get.return_value = mock_response

    result = get_pipeline_workflows(pipeline_id, token)

    assert result == []


@patch("services.circleci.get_pipeline_workflows.requests.get")
def test_get_pipeline_workflows_http_error(mock_get):
    pipeline_id = "test-pipeline-id"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = RuntimeError("Server Error")
    mock_get.return_value = mock_response

    result = get_pipeline_workflows(pipeline_id, token)

    assert result == []

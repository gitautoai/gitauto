from unittest.mock import MagicMock, patch

import pytest

from services.github.workflow_runs.get_workflow_file_runs import get_workflow_file_runs


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "workflow_runs": [
            {"id": 123, "name": "PyTest", "status": "completed"},
            {"id": 456, "name": "PyTest", "status": "completed"},
        ]
    }
    return response


@patch("services.github.workflow_runs.get_workflow_file_runs.get")
def test_get_workflow_file_runs_basic(mock_get, mock_response):
    mock_get.return_value = mock_response

    runs = get_workflow_file_runs(
        owner="gitautoai",
        repo="gitauto",
        workflow_file="pytest.yml",
        token="test-token",
    )

    assert len(runs) == 2
    assert runs[0]["id"] == 123
    mock_get.assert_called_once()
    call_url = mock_get.call_args[1]["url"]
    assert "workflows/pytest.yml/runs" in call_url


@patch("services.github.workflow_runs.get_workflow_file_runs.get")
def test_get_workflow_file_runs_with_branch(mock_get, mock_response):
    mock_get.return_value = mock_response

    get_workflow_file_runs(
        owner="gitautoai",
        repo="gitauto",
        workflow_file="pytest.yml",
        token="test-token",
        branch="main",
    )

    call_url = mock_get.call_args[1]["url"]
    assert "branch=main" in call_url


@patch("services.github.workflow_runs.get_workflow_file_runs.get")
def test_get_workflow_file_runs_pagination(mock_get):
    page1 = MagicMock()
    page1.status_code = 200
    page1.json.return_value = {"workflow_runs": [{"id": i} for i in range(30)]}

    page2 = MagicMock()
    page2.status_code = 200
    page2.json.return_value = {"workflow_runs": [{"id": 100}]}

    mock_get.side_effect = [page1, page2]

    runs = get_workflow_file_runs(
        owner="gitautoai",
        repo="gitauto",
        workflow_file="pytest.yml",
        token="test-token",
        max_pages=2,
    )

    assert len(runs) == 31
    assert mock_get.call_count == 2


@patch("services.github.workflow_runs.get_workflow_file_runs.get")
def test_get_workflow_file_runs_empty(mock_get):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"workflow_runs": []}
    mock_get.return_value = response

    runs = get_workflow_file_runs(
        owner="gitautoai",
        repo="gitauto",
        workflow_file="pytest.yml",
        token="test-token",
    )

    assert runs == []

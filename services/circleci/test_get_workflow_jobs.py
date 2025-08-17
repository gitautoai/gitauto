"""Unit tests for get_circleci_workflow_jobs using mocked data."""

import json
from unittest.mock import patch, Mock

from config import UTF8
from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs


@patch("services.circleci.get_workflow_jobs.get")
def test_get_workflow_jobs_with_valid_token(mock_get):
    """Test getting workflow jobs with valid token and workflow ID."""
    workflow_id = "test-workflow-id"
    token = "test-token"

    # Load mock response from saved payload
    with open("payloads/circleci/workflow_jobs.json", "r", encoding=UTF8) as f:
        job_items = json.load(f)

    mock_response_data = {"items": job_items, "next_page_token": None}

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_get.return_value = mock_response

    result = get_circleci_workflow_jobs(workflow_id, token)

    # Should return a list of jobs
    assert isinstance(result, list)
    assert len(result) >= 2

    # Check that jobs have expected structure
    job_names = [job["name"] for job in result]
    assert "Quick Validation Tests (Should Pass)" in job_names
    assert "Stress Tests (Intentional Failure)" in job_names

    # Check for failed job
    failed_jobs = [job for job in result if job["status"] == "failed"]
    assert len(failed_jobs) >= 1

    # Check for successful job
    success_jobs = [job for job in result if job["status"] == "success"]
    assert len(success_jobs) >= 1


@patch("services.circleci.get_workflow_jobs.get")
def test_get_workflow_jobs_without_token(mock_get):
    """Test getting workflow jobs without token."""
    workflow_id = "test-workflow-id"

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("Unauthorized")
    mock_get.return_value = mock_response

    result = get_circleci_workflow_jobs(workflow_id, "")

    # Should return empty list due to exception handling
    assert result == []


@patch("services.circleci.get_workflow_jobs.get")
def test_get_workflow_jobs_with_invalid_workflow_id(mock_get):
    """Test getting workflow jobs with invalid workflow ID."""
    workflow_id = "invalid-workflow-id-123"
    token = "test-token"

    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_circleci_workflow_jobs(workflow_id, token)

    # Should return empty list for 404
    assert result == []

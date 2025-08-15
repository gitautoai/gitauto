"""Unit tests for get_circleci_workflow_jobs using real data."""

import os
import pytest

from services.circleci.get_workflow_jobs import get_circleci_workflow_jobs


def test_get_workflow_jobs_with_valid_token():
    """Test getting workflow jobs with valid token and workflow ID."""
    # Real workflow ID from the CircleCI URL in the payload
    workflow_id = "772ddda7-d6b7-49ad-9123-108d9f8164b5"

    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        pytest.skip("CIRCLECI_TOKEN not set")

    result = get_circleci_workflow_jobs(workflow_id, token)

    # Should return a list of jobs
    assert isinstance(result, list)
    assert len(result) >= 2  # We have test-pass and test-fail jobs

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


def test_get_workflow_jobs_without_token():
    """Test getting workflow jobs without token."""
    workflow_id = "772ddda7-d6b7-49ad-9123-108d9f8164b5"

    result = get_circleci_workflow_jobs(workflow_id, None)

    # Should return empty list for private repo without token
    assert result == []


def test_get_workflow_jobs_with_invalid_workflow_id():
    """Test getting workflow jobs with invalid workflow ID."""
    workflow_id = "invalid-workflow-id-123"

    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        pytest.skip("CIRCLECI_TOKEN not set")

    result = get_circleci_workflow_jobs(workflow_id, token)

    # Should return empty list for invalid workflow
    assert result == []

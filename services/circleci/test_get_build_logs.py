"""Unit tests for get_circleci_build_logs using real data."""

import os
import pytest

from services.circleci.get_build_logs import get_circleci_build_logs


def test_get_build_logs_with_valid_token():
    """Test getting build logs with valid token and project slug."""
    # Real project slug from the CircleCI URL in the payload
    project_slug = "circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s"

    # Real build number from a failed job
    build_number = 13  # This should be the "Stress Tests (Intentional Failure)" job

    # Get token from environment
    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        pytest.skip("CIRCLECI_TOKEN not set")

    result = get_circleci_build_logs(project_slug, build_number, token)

    # For build 13 (failed job), we expect error logs
    assert isinstance(result, str)
    assert "CircleCI Build Log" in result
    assert "ERROR" in result


def test_get_build_logs_without_token():
    """Test getting build logs without token (public repo scenario)."""
    project_slug = "circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s"
    build_number = 13

    result = get_circleci_build_logs(project_slug, build_number, None)

    # Private repo without token should return 404
    assert result == 404


def test_get_build_logs_with_invalid_build_number():
    """Test getting build logs with invalid build number."""
    project_slug = "circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s"
    build_number = 99999

    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        pytest.skip("CIRCLECI_TOKEN not set")

    result = get_circleci_build_logs(project_slug, build_number, token)

    assert result == 404


def test_get_build_logs_successful_build():
    """Test getting logs from a successful build (should return None)."""
    project_slug = "circleci/J2wtzLah5rmzRnx6qn4RyQ/UUb5FLNgQCnif8mB6mQn7s"
    build_number = 14

    token = os.environ.get("CIRCLECI_TOKEN")
    if not token:
        pytest.skip("CIRCLECI_TOKEN not set")

    result = get_circleci_build_logs(project_slug, build_number, token)

    # Successful build should return None (no error logs)
    assert result is None

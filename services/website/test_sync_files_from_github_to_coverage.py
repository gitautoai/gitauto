# pylint: disable=unused-argument
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from services.website.sync_files_from_github_to_coverage import (
    sync_files_from_github_to_coverage,
)


@pytest.fixture
def mock_verify_api_key():
    with patch(
        "services.website.sync_files_from_github_to_coverage.verify_api_key"
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_efs_dir():
    with patch(
        "services.website.sync_files_from_github_to_coverage.get_efs_dir",
        return_value="/mnt/efs/test-owner/test-repo",
    ) as mock:
        yield mock


@pytest.fixture
def mock_get_file_tree(mock_get_efs_dir):
    with patch(
        "services.website.sync_files_from_github_to_coverage.get_file_tree"
    ) as mock:
        yield mock


@pytest.fixture
def mock_upsert_coverages():
    with patch(
        "services.website.sync_files_from_github_to_coverage.upsert_coverages"
    ) as mock:
        yield mock


@pytest.fixture
def mock_delete_stale_coverages():
    with patch(
        "services.website.sync_files_from_github_to_coverage.delete_stale_coverages"
    ) as mock:
        mock.return_value = 0
        yield mock


def test_sync_upserts_files(
    mock_verify_api_key,
    mock_get_file_tree,
    mock_upsert_coverages,
    mock_delete_stale_coverages,
):
    mock_get_file_tree.return_value = [
        {"path": "src/main.py", "sha": "abc123", "size": 100, "type": "blob"},
        {"path": "src/utils.py", "sha": "def456", "size": 200, "type": "blob"},
    ]

    sync_files_from_github_to_coverage(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        owner_id=123,
        repo_id=456,
        user_name="test-user",
        api_key="test-api-key",
    )

    mock_verify_api_key.assert_called_once_with("test-api-key")
    mock_upsert_coverages.assert_called_once()
    records = mock_upsert_coverages.call_args[0][0]
    assert len(records) == 2
    assert records[0]["full_path"] == "src/main.py"
    assert records[0]["file_size"] == 100
    assert records[0]["created_by"] == "test-user"
    assert records[0]["updated_by"] == "test-user"
    assert records[1]["full_path"] == "src/utils.py"


def test_sync_calls_delete_stale(
    mock_verify_api_key,
    mock_get_file_tree,
    mock_upsert_coverages,
    mock_delete_stale_coverages,
):
    mock_get_file_tree.return_value = []

    sync_files_from_github_to_coverage(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        owner_id=123,
        repo_id=456,
        user_name="test-user",
        api_key="test-api-key",
    )

    mock_delete_stale_coverages.assert_called_once_with(
        owner_id=123,
        repo_id=456,
        current_files=set(),
    )


def test_sync_filters_directories(
    mock_verify_api_key,
    mock_get_file_tree,
    mock_upsert_coverages,
    mock_delete_stale_coverages,
):
    mock_get_file_tree.return_value = [
        {"path": "src", "sha": "dir123", "type": "tree"},
        {"path": "src/main.py", "sha": "abc123", "size": 100, "type": "blob"},
    ]

    sync_files_from_github_to_coverage(
        owner="test-owner",
        repo="test-repo",
        branch="main",
        owner_id=123,
        repo_id=456,
        user_name="test-user",
        api_key="test-api-key",
    )

    records = mock_upsert_coverages.call_args[0][0]
    assert len(records) == 1
    assert records[0]["full_path"] == "src/main.py"


def test_sync_invalid_api_key(mock_get_file_tree):
    with patch(
        "services.website.sync_files_from_github_to_coverage.verify_api_key",
        side_effect=HTTPException(status_code=401, detail="Invalid API key"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            sync_files_from_github_to_coverage(
                owner="test-owner",
                repo="test-repo",
                branch="main",
                owner_id=123,
                repo_id=456,
                user_name="test-user",
                api_key="invalid-key",
            )
        assert exc_info.value.status_code == 401


def test_sync_skips_verification_without_api_key(
    mock_get_file_tree,
    mock_upsert_coverages,
    mock_delete_stale_coverages,
):
    """When api_key is None (internal Lambda calls), verification is skipped."""
    mock_get_file_tree.return_value = [
        {"path": "src/main.py", "sha": "abc123", "size": 100, "type": "blob"},
    ]

    with patch(
        "services.website.sync_files_from_github_to_coverage.verify_api_key"
    ) as mock_verify:
        sync_files_from_github_to_coverage(
            owner="test-owner",
            repo="test-repo",
            branch="main",
            owner_id=123,
            repo_id=456,
            user_name="test-user",
        )

        mock_verify.assert_not_called()
        mock_upsert_coverages.assert_called_once()

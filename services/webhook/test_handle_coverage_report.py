from unittest.mock import patch

from config import UTF8
from services.webhook.handle_coverage_report import handle_coverage_report


def test_handle_coverage_report_with_python_sample():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch="main",
            user_name="test-user",
        )

        assert result is True
        mock_upsert_cov.assert_called_once()
        mock_upsert_repo.assert_called_once()

        # Verify get_coverages was called with owner_id
        mock_get_cov.assert_called_once()
        call_kwargs = mock_get_cov.call_args.kwargs
        assert call_kwargs["owner_id"] == 12345
        assert call_kwargs["repo_id"] == 67890


def test_handle_coverage_report_with_coverage_report_artifact():
    """Test handling coverage with artifact named 'coverage-report'"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-report.lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch="main",
            user_name="test-user",
        )

        assert result is True
        mock_download.assert_called_once()


def test_handle_coverage_report_with_default_artifact_name():
    """Test handling coverage with default artifact name 'artifact'"""
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 456, "name": "artifact.lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=333,
            head_branch="main",
            user_name="test-user",
        )

        assert result is True
        mock_download.assert_called_once()


def test_handle_coverage_report_skips_non_coverage_artifacts():
    """Test that non-coverage artifacts are skipped"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [
            {"id": 123, "name": "build-logs"},
            {"id": 456, "name": "test-results"},
        ]

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=444,
            head_branch="main",
            user_name="test-user",
        )

        assert result is None
        mock_download.assert_not_called()


def test_handle_coverage_report_with_javascript_sample():
    with open("payloads/lcov/lcov-javascript-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 456, "name": "jest-coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch="main",
            user_name="test-user",
        )

        assert result is True
        mock_upsert_cov.assert_called_once()
        mock_upsert_repo.assert_called_once()


def test_handle_coverage_report_with_null_head_branch():
    """Test handling coverage report when head_branch is None (detached HEAD state)"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo, patch(
        "services.webhook.handle_coverage_report.logging"
    ) as mock_logging:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        # Act - pass None for head_branch
        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch=None,  # Testing null head_branch
            user_name="test-user",
        )

        # Assert
        assert result is True
        mock_upsert_cov.assert_called_once()

        # Verify the branch_name was set to "detached" in the upserted data
        upsert_call_args = mock_upsert_cov.call_args[0][0]
        assert all(item.get("branch_name") == "detached" for item in upsert_call_args)

        # Verify logging was called
        mock_logging.info.assert_any_call(
            "No branch context for coverage report (run_id: %s, source: %s). Using 'detached'.",
            222,
            "github",
        )


def test_handle_coverage_report_circleci():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_circleci_token"
    ) as mock_get_token, patch(
        "services.webhook.handle_coverage_report.get_circleci_workflow_ids_from_check_suite"
    ) as mock_workflow_ids, patch(
        "services.webhook.handle_coverage_report.get_circleci_workflow_jobs"
    ) as mock_jobs, patch(
        "services.webhook.handle_coverage_report.get_circleci_job_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_circleci_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_get_token.return_value = {"token": "circle-token"}
        mock_workflow_ids.return_value = ["workflow-123"]
        mock_jobs.return_value = [
            {"job_number": 1, "name": "test-job", "status": "success"}
        ]
        mock_artifacts.return_value = [
            {"path": "lcov.info", "url": "http://example.com/lcov.info"}
        ]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=333,
            head_branch="main",
            user_name="test-user",
            source="circleci",
        )

        assert result is True
        mock_upsert_cov.assert_called_once()
        mock_upsert_repo.assert_called_once()

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


def test_handle_coverage_report_circleci():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_circleci_token"
    ) as mock_get_token, patch(
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

        mock_get_token.return_value = {"token": "circle-token"}
        mock_jobs.return_value = [{"job_number": 1, "status": "success"}]
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

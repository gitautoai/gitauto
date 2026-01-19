from unittest.mock import patch

from config import UTF8
from services.webhook.handle_coverage_report import handle_coverage_report


def test_handle_coverage_report_with_python_sample():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
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

        # Verify upsert_repo_coverage was called with count fields
        repo_coverage_data = mock_upsert_repo.call_args[0][0]
        assert repo_coverage_data["lines_covered"] == 4918
        assert repo_coverage_data["lines_total"] == 6721
        assert repo_coverage_data["functions_covered"] == 195
        assert repo_coverage_data["functions_total"] == 242
        assert repo_coverage_data["branches_covered"] == 1009
        assert repo_coverage_data["branches_total"] == 1830

        # Verify upsert_coverages does NOT include fields that don't exist in coverages table
        coverage_records = mock_upsert_cov.call_args[0][0]
        excluded_fields = [
            "lines_covered",
            "lines_total",
            "functions_covered",
            "functions_total",
            "branches_covered",
            "branches_total",
        ]
        for record in coverage_records:
            for field in excluded_fields:
                assert (
                    field not in record
                ), f"Field '{field}' should not be in coverage record"


def test_handle_coverage_report_with_coverage_report_artifact():
    """Test handling coverage with artifact named 'coverage-report'"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-report.lcov.info"}]
        mock_download.return_value = sample_lcov
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
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 456, "name": "artifact.lcov.info"}]
        mock_download.return_value = sample_lcov
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
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
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
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 456, "name": "jest-coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
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

        # Verify upsert_repo_coverage was called with count fields
        repo_coverage_data = mock_upsert_repo.call_args[0][0]
        assert repo_coverage_data["lines_covered"] == 141
        assert repo_coverage_data["lines_total"] == 3941
        assert repo_coverage_data["functions_covered"] == 40
        assert repo_coverage_data["functions_total"] == 1484
        assert repo_coverage_data["branches_covered"] == 43
        assert repo_coverage_data["branches_total"] == 1696


def test_handle_coverage_report_with_null_head_branch():
    """Test handling coverage report when head_branch is None (detached HEAD state)

    With target branch checking, detached HEAD builds are skipped since
    'detached' != target_branch.
    """
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.logger"
    ) as mock_logger:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch=None,
            user_name="test-user",
        )

        assert result is None
        mock_logger.info.assert_any_call(
            "No branch context for coverage report (run_id: %s, source: %s). Using 'detached'.",
            222,
            "github",
        )
        mock_logger.info.assert_any_call(
            "Skipping saving coverage to Supabase: head_branch=%s != target_branch=%s",
            "detached",
            "main",
        )


def test_handle_coverage_report_circleci():
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
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
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_get_token.return_value = {"token": "circle-token"}
        mock_workflow_ids.return_value = ["workflow-123"]
        mock_jobs.return_value = [
            {"job_number": 1, "name": "test-job", "status": "success"}
        ]
        mock_artifacts.return_value = [
            {"path": "lcov.info", "url": "http://example.com/lcov.info"}
        ]
        mock_download.return_value = sample_lcov
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


def test_scenario1_file_exists_and_in_lcov_updates_coverage():
    """Scenario 1: File exists in repo AND is in lcov → Update with actual coverage"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_all_coverages"
    ) as mock_all_cov, patch(
        "services.webhook.handle_coverage_report.delete_coverages_by_paths"
    ) as mock_delete:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True
        mock_tree.return_value = [
            {"path": "services/github/github_manager.py", "type": "blob"},
        ]
        mock_all_cov.return_value = []

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
        upsert_data = mock_upsert_cov.call_args[0][0]
        assert len(upsert_data) > 0
        mock_delete.assert_not_called()


def test_scenario2_file_exists_but_not_in_lcov_not_touched():
    """Scenario 2: File exists in repo but NOT in lcov → Don't touch existing coverage"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_all_coverages"
    ) as mock_all_cov, patch(
        "services.webhook.handle_coverage_report.delete_coverages_by_paths"
    ) as mock_delete:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True
        mock_tree.return_value = [
            {"path": "services/github/github_manager.py", "type": "blob"},
            {"path": "src/components/Table/index.tsx", "type": "blob"},
        ]
        mock_all_cov.return_value = [
            {
                "full_path": "src/components/Table/index.tsx",
                "statement_coverage": 100.0,
            },
        ]

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
        upsert_data = mock_upsert_cov.call_args[0][0]
        upserted_paths = [item["full_path"] for item in upsert_data]
        assert "src/components/Table/index.tsx" not in upserted_paths
        mock_delete.assert_not_called()


def test_scenario3_file_deleted_from_repo_removes_coverage():
    """Scenario 3: File was deleted from repo → Remove coverage record"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_all_coverages"
    ) as mock_all_cov, patch(
        "services.webhook.handle_coverage_report.delete_coverages_by_paths"
    ) as mock_delete:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": "main"}
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True
        mock_upsert_repo.return_value = True
        mock_tree.return_value = [
            {"path": "services/github/github_manager.py", "type": "blob"},
        ]
        mock_all_cov.return_value = [
            {"full_path": "deleted/old_file.py", "statement_coverage": 50.0},
        ]

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
        mock_delete.assert_called_once_with(
            owner_id=12345,
            repo_id=67890,
            file_paths=["deleted/old_file.py"],
        )


def test_handle_coverage_report_fallback_to_default_branch():
    """Test that empty target_branch falls back to GitHub's default branch"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_repository"
    ) as mock_repo, patch(
        "services.webhook.handle_coverage_report.get_default_branch"
    ) as mock_default, patch(
        "services.webhook.handle_coverage_report.logger"
    ) as mock_logger:

        mock_token.return_value = "fake-token"
        mock_repo.return_value = {"target_branch": ""}
        mock_default.return_value = ("main", "abc123")

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=222,
            head_branch="feature-branch",
            user_name="test-user",
        )

        assert result is None
        mock_default.assert_called_once_with(
            owner="test-owner", repo="test-repo", token="fake-token"
        )
        mock_logger.info.assert_any_call(
            "Skipping saving coverage to Supabase: head_branch=%s != target_branch=%s",
            "feature-branch",
            "main",
        )

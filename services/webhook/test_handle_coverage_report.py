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

        assert result is True
        mock_upsert_cov.assert_called_once()

        upsert_call_args = mock_upsert_cov.call_args[0][0]
        assert all(item.get("branch_name") == "detached" for item in upsert_call_args)

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


def test_handle_coverage_report_circleci_no_token():
    """Test CircleCI source when no token is found - covers lines 59-61"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_circleci_token"
    ) as mock_get_token:

        mock_token.return_value = "fake-token"
        mock_get_token.return_value = None

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

        assert result is None


def test_handle_coverage_report_circleci_no_workflow_ids():
    """Test CircleCI source when no workflow IDs are found - covers lines 66-70"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_circleci_token"
    ) as mock_get_token, patch(
        "services.webhook.handle_coverage_report.get_circleci_workflow_ids_from_check_suite"
    ) as mock_workflow_ids:

        mock_token.return_value = "fake-token"
        mock_get_token.return_value = {"token": "circle-token"}
        mock_workflow_ids.return_value = None

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

        assert result is None


def test_handle_coverage_report_circleci_failed_job():
    """Test CircleCI with failed job status - covers lines 85-86"""
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
    ) as mock_artifacts:

        mock_token.return_value = "fake-token"
        mock_get_token.return_value = {"token": "circle-token"}
        mock_workflow_ids.return_value = ["workflow-123"]
        mock_jobs.return_value = [
            {"job_number": 1, "name": "test-job", "status": "failed"}
        ]

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

        assert result is None
        mock_artifacts.assert_not_called()


def test_handle_coverage_report_invalid_source():
    """Test with invalid source parameter - covers line 95"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token:

        mock_token.return_value = "fake-token"

        result = handle_coverage_report(
            owner_id=12345,
            owner_name="test-owner",
            repo_id=67890,
            repo_name="test-repo",
            installation_id=111,
            run_id=333,
            head_branch="main",
            user_name="test-user",
            source="invalid-source",
        )

        assert result is None


def test_handle_coverage_report_circleci_no_circle_token_in_loop():
    """Test CircleCI artifact download when circle_token is None - covers lines 125-126"""
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
    ) as mock_download:

        mock_token.return_value = "fake-token"
        mock_get_token.return_value = {"token": None}
        mock_workflow_ids.return_value = ["workflow-123"]
        mock_jobs.return_value = [
            {"job_number": 1, "name": "test-job", "status": "success"}
        ]
        mock_artifacts.return_value = [
            {"path": "lcov.info", "url": "http://example.com/lcov.info"}
        ]

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

        assert result is None
        mock_download.assert_not_called()


def test_handle_coverage_report_empty_artifact_content():
    """Test when artifact download returns empty content - covers lines 132-134"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = None

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

        assert result is None


def test_handle_coverage_report_no_parsed_coverage():
    """Test when parse_lcov_coverage returns None - covers line 154"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = "invalid lcov content"
        mock_parse.return_value = None

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

        assert result is None


def test_handle_coverage_report_with_uncovered_files():
    """Test adding uncovered source files - covers lines 175-177"""
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
        "services.webhook.handle_coverage_report.is_code_file"
    ) as mock_is_code, patch(
        "services.webhook.handle_coverage_report.is_test_file"
    ) as mock_is_test, patch(
        "services.webhook.handle_coverage_report.is_type_file"
    ) as mock_is_type, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = sample_lcov
        mock_tree.return_value = [
            {"path": "src/uncovered.py", "type": "blob"},
            {"path": "src/covered.py", "type": "blob"},
        ]
        mock_is_code.side_effect = lambda f: f.endswith(".py")
        mock_is_test.return_value = False
        mock_is_type.return_value = False
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
        upsert_call_args = mock_upsert_cov.call_args[0][0]
        uncovered_files = [
            item for item in upsert_call_args if item.get("line_coverage") == 0.0
        ]
        assert len(uncovered_files) > 0


def test_handle_coverage_report_with_duplicate_coverage():
    """Test handling duplicate coverage entries - covers lines 198-200"""
    with open("payloads/lcov/lcov-python-sample.info", "r", encoding=UTF8) as f:
        sample_lcov = f.read()

    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse, patch(
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
        mock_parse.return_value = [
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/test.py",
                "statement_coverage": 80.0,
                "function_coverage": 90.0,
                "branch_coverage": 70.0,
                "line_coverage": 85.0,
                "path_coverage": 70.0,
                "uncovered_lines": "10,20",
                "uncovered_functions": "",
                "uncovered_branches": "",
            },
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/test.py",
                "statement_coverage": 85.0,
                "function_coverage": 95.0,
                "branch_coverage": 75.0,
                "line_coverage": 90.0,
                "path_coverage": 75.0,
                "uncovered_lines": "10",
                "uncovered_functions": "",
                "uncovered_branches": "",
            },
        ]
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


def test_handle_coverage_report_with_existing_record():
    """Test with existing coverage records"""
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
        mock_get_cov.return_value = {
            "services/github/artifacts/download_artifact.py": {
                "id": 1,
                "created_at": "2023-01-01",
                "updated_at": "2023-01-02",
                "created_by": "old-user",
            }
        }
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
        upsert_call_args = mock_upsert_cov.call_args[0][0]
        for item in upsert_call_args:
            assert "id" not in item
            assert "created_at" not in item
            assert "updated_at" not in item


def test_handle_coverage_report_with_100_percent_coverage():
    """Test handling 100% coverage fields - lines 230-235"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse, patch(
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
        mock_download.return_value = "lcov content"
        mock_parse.return_value = [
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/perfect.py",
                "statement_coverage": 100.0,
                "function_coverage": 100.0,
                "branch_coverage": 100.0,
                "line_coverage": 100.0,
                "path_coverage": 100.0,
                "uncovered_lines": "",
                "uncovered_functions": "",
                "uncovered_branches": "",
            }
        ]
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
        upsert_call_args = mock_upsert_cov.call_args[0][0]
        for item in upsert_call_args:
            if item.get("line_coverage") == 100:
                assert item.get("uncovered_lines") is None
            if item.get("function_coverage") == 100:
                assert item.get("uncovered_functions") is None
            if item.get("branch_coverage") == 100:
                assert item.get("uncovered_branches") is None


def test_handle_coverage_report_with_non_serializable_item():
    """Test handling non-serializable items - covers lines 243-246"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.upsert_coverages"
    ) as mock_upsert_cov, patch(
        "services.webhook.handle_coverage_report.upsert_repo_coverage"
    ) as mock_upsert_repo, patch(
        "services.webhook.handle_coverage_report.json.dumps"
    ) as mock_json:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = "lcov content"
        mock_parse.return_value = [
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/test.py",
                "statement_coverage": 80.0,
                "function_coverage": 90.0,
                "branch_coverage": 70.0,
                "line_coverage": 85.0,
                "path_coverage": 70.0,
                "uncovered_lines": "10,20",
                "uncovered_functions": "",
                "uncovered_branches": "",
            }
        ]
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_json.side_effect = TypeError("Not serializable")

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

        assert result is None
        mock_upsert_cov.assert_not_called()


def test_handle_coverage_report_no_valid_upsert_data():
    """Test when no valid items to upsert - covers lines 248-250"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse, patch(
        "services.webhook.handle_coverage_report.get_file_tree"
    ) as mock_tree, patch(
        "services.webhook.handle_coverage_report.get_coverages"
    ) as mock_get_cov, patch(
        "services.webhook.handle_coverage_report.json.dumps"
    ) as mock_json:

        mock_token.return_value = "fake-token"
        mock_artifacts.return_value = [{"id": 123, "name": "coverage-lcov.info"}]
        mock_download.return_value = "lcov content"
        mock_parse.return_value = [
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/test.py",
                "statement_coverage": 80.0,
                "function_coverage": 90.0,
                "branch_coverage": 70.0,
                "line_coverage": 85.0,
                "path_coverage": 70.0,
                "uncovered_lines": "10,20",
                "uncovered_functions": "",
                "uncovered_branches": "",
            }
        ]
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_json.side_effect = ValueError("Invalid JSON")

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

        assert result is None


def test_handle_coverage_report_without_repo_coverage():
    """Test when no repository-level coverage exists - covers line 258"""
    with patch(
        "services.webhook.handle_coverage_report.get_installation_access_token"
    ) as mock_token, patch(
        "services.webhook.handle_coverage_report.get_workflow_artifacts"
    ) as mock_artifacts, patch(
        "services.webhook.handle_coverage_report.download_artifact"
    ) as mock_download, patch(
        "services.webhook.handle_coverage_report.parse_lcov_coverage"
    ) as mock_parse, patch(
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
        mock_download.return_value = "lcov content"
        mock_parse.return_value = [
            {
                "package_name": None,
                "language": "python",
                "level": "file",
                "full_path": "src/test.py",
                "statement_coverage": 80.0,
                "function_coverage": 90.0,
                "branch_coverage": 70.0,
                "line_coverage": 85.0,
                "path_coverage": 70.0,
                "uncovered_lines": "10,20",
                "uncovered_functions": "",
                "uncovered_branches": "",
            }
        ]
        mock_tree.return_value = []
        mock_get_cov.return_value = {}
        mock_upsert_cov.return_value = True

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
        mock_upsert_repo.assert_not_called()


def test_handle_coverage_report_circleci_with_coverage_report_artifact():
    """Test CircleCI with coverage-report artifact name"""
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
            {"path": "coverage-report", "url": "http://example.com/coverage-report"}
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
        mock_download.assert_called_once()

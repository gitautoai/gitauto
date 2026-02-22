import os
import unittest
from unittest.mock import patch, MagicMock

import pytest

from services.supabase.issues.get_issue import get_issue


def _mock_response(data):
    mock = MagicMock()
    mock.data = data
    return mock


class TestGetIssue(unittest.TestCase):
    def setUp(self):
        self.sample_issue_data = {
            "id": 1,
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "issue_number": 123,
            "installation_id": 456,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 789,
            "repo_id": 101112,
            "created_by": "test-user",
            "run_id": None,
        }

        self.test_params = {
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "pr_number": 123,
        }

    def _setup_supabase_mock(self, mock_supabase, return_data):
        mock_chain = (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        )
        mock_chain.execute.return_value = _mock_response(return_data)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_success_with_data(self, mock_supabase):
        mock_issue_data = {
            "id": 1,
            "owner_type": "Organization",
            "owner_name": "test-owner",
            "repo_name": "test-repo",
            "issue_number": 123,
            "installation_id": 456,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 789,
            "repo_id": 101112,
            "created_by": "test-user",
            "run_id": None,
        }

        self._setup_supabase_mock(mock_supabase, [mock_issue_data])

        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            pr_number=123,
        )

        assert result is not None
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["owner_type"], "Organization")
        mock_supabase.table.assert_called_once_with(table_name="issues")

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_no_data_found(self, mock_supabase):
        self._setup_supabase_mock(mock_supabase, [])

        result = get_issue(
            owner_type="Organization",
            owner_name="nonexistent-owner",
            repo_name="nonexistent-repo",
            pr_number=999,
        )

        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_different_owner_types(self, mock_supabase):
        mock_issue_data = {
            "id": 2,
            "owner_type": "User",
            "owner_name": "individual-user",
            "repo_name": "personal-repo",
            "issue_number": 789,
            "installation_id": 123,
            "merged": True,
            "created_at": "2024-02-01T00:00:00Z",
            "owner_id": 456,
            "repo_id": 789012,
            "created_by": "individual-user",
            "run_id": 999,
        }

        self._setup_supabase_mock(mock_supabase, [mock_issue_data])

        result = get_issue(
            owner_type="User",
            owner_name="individual-user",
            repo_name="personal-repo",
            pr_number=789,
        )

        assert result is not None
        self.assertEqual(result["owner_type"], "User")
        self.assertEqual(result["merged"], True)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_database_exception(self, mock_supabase):
        mock_supabase.table.side_effect = Exception("Database connection error")

        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            pr_number=123,
        )

        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_zero_pr_number(self, mock_supabase):
        issue_data = self.sample_issue_data.copy()
        issue_data["issue_number"] = 0
        self._setup_supabase_mock(mock_supabase, [issue_data])

        result = get_issue(
            owner_type="Organization",
            owner_name="test-owner",
            repo_name="test-repo",
            pr_number=0,
        )

        assert result is not None
        self.assertEqual(result["issue_number"], 0)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_large_pr_number(self, mock_supabase):
        large_pr_number = 999999999
        issue_data = self.sample_issue_data.copy()
        issue_data["issue_number"] = large_pr_number
        self._setup_supabase_mock(mock_supabase, [issue_data])

        result = get_issue(
            owner_type="User",
            owner_name="test-user",
            repo_name="test-repo",
            pr_number=large_pr_number,
        )

        assert result is not None
        self.assertEqual(result["issue_number"], large_pr_number)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_returns_first_result_only(self, mock_supabase):
        first_issue = self.sample_issue_data.copy()
        second_issue = self.sample_issue_data.copy()
        second_issue["id"] = 2

        self._setup_supabase_mock(mock_supabase, [first_issue, second_issue])

        result = get_issue(**self.test_params)

        assert result is not None
        self.assertEqual(result["id"], 1)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_returns_correct_data_structure(self, mock_supabase):
        self._setup_supabase_mock(mock_supabase, [self.sample_issue_data])

        result = get_issue(**self.test_params)

        self.assertEqual(result, self.sample_issue_data)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_none_values(self, mock_supabase):
        issue_data_with_nones = self.sample_issue_data.copy()
        issue_data_with_nones["run_id"] = None
        issue_data_with_nones["created_by"] = None

        self._setup_supabase_mock(mock_supabase, [issue_data_with_nones])

        result = get_issue(**self.test_params)

        assert result is not None
        self.assertIsNone(result["run_id"])
        self.assertIsNone(result["created_by"])

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_supabase_execute_exception(self, mock_supabase):
        mock_chain = (
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value
        )
        mock_chain.execute.side_effect = Exception("Supabase execute error")

        result = get_issue(**self.test_params)

        self.assertIsNone(result)

    @patch("services.supabase.issues.get_issue.supabase")
    def test_get_issue_with_minimal_required_fields(self, mock_supabase):
        minimal_issue_data = {
            "id": 999,
            "owner_type": "Organization",
            "owner_name": "minimal-owner",
            "repo_name": "minimal-repo",
            "issue_number": 1,
            "installation_id": 123,
            "merged": False,
            "created_at": "2024-01-01T00:00:00Z",
            "owner_id": 456,
            "repo_id": 789,
        }

        self._setup_supabase_mock(mock_supabase, [minimal_issue_data])

        result = get_issue(
            owner_type="Organization",
            owner_name="minimal-owner",
            repo_name="minimal-repo",
            pr_number=1,
        )

        assert result is not None
        self.assertEqual(result["id"], 999)


@pytest.mark.skipif(bool(os.environ.get("CI")), reason="Integration test")
def test_get_issue_integration():
    result = get_issue("Organization", "gitautoai", "website", 323)
    assert result is not None
    assert result["owner_name"] == "gitautoai"
    assert result["issue_number"] == 323

    result = get_issue("Organization", "nonexistent", "nonexistent", 999999)
    assert result is None


if __name__ == "__main__":
    unittest.main()

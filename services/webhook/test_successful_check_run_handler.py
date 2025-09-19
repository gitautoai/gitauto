from unittest.mock import MagicMock, patch

from services.webhook.successful_check_run_handler import handle_successful_check_run


def test_handle_successful_check_run_with_pr():
    payload = {
        "check_run": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_run_handler.supabase"
    ) as mock_supabase:
        # Setup mock chain for select
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[{"id": 100}])

        # Setup mock chain for update
        mock_update = MagicMock()
        mock_update_eq = MagicMock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_update_eq

        # Execute
        handle_successful_check_run(payload)

        # Verify select was called
        mock_table.select.assert_called_once_with("id")
        mock_select.eq.assert_called_once_with("repo_id", 871345449)
        mock_eq1.eq.assert_called_once_with("pr_number", 123)
        mock_eq2.eq.assert_called_once_with("owner_id", 4620828)

        # Verify update was called
        mock_table.update.assert_called_once_with({"is_test_passed": True})
        mock_update.eq.assert_called_once_with("id", 100)
        mock_update_eq.execute.assert_called_once()


def test_handle_successful_check_run_without_pr():
    payload = {
        "check_run": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_run_handler.supabase"
    ) as mock_supabase:
        # Execute
        handle_successful_check_run(payload)

        # Verify no database call was made
        mock_supabase.table.assert_not_called()


def test_handle_successful_check_run_no_usage_record_found():
    payload = {
        "check_run": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_run_handler.supabase"
    ) as mock_supabase:
        # Setup mock to return empty data
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_eq3 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.eq.return_value = mock_eq3
        mock_eq3.order.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(data=[])

        # Execute
        handle_successful_check_run(payload)

        # Verify select was called but update was not
        mock_table.select.assert_called_once()
        mock_table.update.assert_not_called()


def test_handle_successful_check_run_with_exception():
    payload = {
        "check_run": {
            "id": 31710113401,
            "name": "test-job",
            "conclusion": "success",
            "pull_requests": [
                {
                    "url": "https://api.github.com/repos/test-owner/test-repo/pulls/123",
                    "id": 2131041354,
                    "number": 123,
                }
            ],
        },
        "repository": {
            "id": 871345449,
            "name": "test-repo",
            "owner": {
                "id": 4620828,
                "login": "test-owner",
            },
        },
    }

    with patch(
        "services.webhook.successful_check_run_handler.supabase"
    ) as mock_supabase:
        # Setup mock to raise exception
        mock_supabase.table.side_effect = Exception("Database error")

        # Execute - should not raise due to handle_exceptions decorator
        result = handle_successful_check_run(payload)

        # Verify it returns None (default_return_value)
        assert result is None

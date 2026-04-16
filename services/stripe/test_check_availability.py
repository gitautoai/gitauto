from unittest.mock import patch

import pytest

from constants.models import MAX_CREDIT_COST_USD
from services.stripe.check_availability import check_availability


class TestCheckAvailability:

    @pytest.fixture
    def mock_dependencies(self):
        with patch(
            "services.stripe.check_availability.get_billing_type"
        ) as mock_get_billing_type, patch(
            "services.stripe.check_availability.get_owner"
        ) as mock_get_owner, patch(
            "services.stripe.check_availability.trigger_auto_reload"
        ) as mock_trigger_auto_reload, patch(
            "services.stripe.check_availability.get_insufficient_credits_message"
        ) as mock_get_insufficient_credits_message:

            yield {
                "get_billing_type": mock_get_billing_type,
                "get_owner": mock_get_owner,
                "trigger_auto_reload": mock_trigger_auto_reload,
                "get_insufficient_credits_message": mock_get_insufficient_credits_message,
            }

    def test_exception_billing_type_allows_unlimited_access(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "exception"

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["billing_type"] == "exception"
        assert result["log_message"] == "Exception owner - unlimited access."
        assert result["user_message"] == ""
        assert result["credit_balance_usd"] == 0

    def test_credit_billing_type_with_sufficient_credits(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        balance = MAX_CREDIT_COST_USD * 10
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": balance,
            "auto_reload_enabled": False,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == balance
        assert result["log_message"] == f"Checked credit balance. ${balance} remaining."
        assert result["user_message"] == ""
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_credit_billing_type_with_insufficient_credits(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {"credit_balance_usd": 0}
        mock_dependencies["get_insufficient_credits_message"].return_value = (
            "Insufficient credits"
        )

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == 0
        assert result["user_message"] == "Insufficient credits"
        assert result["log_message"] == "Insufficient credits for test_owner/test_repo"
        mock_dependencies["get_insufficient_credits_message"].assert_called_once_with(
            user_name="test_sender"
        )

    def test_credit_billing_type_with_no_owner_data(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = None
        mock_dependencies["get_insufficient_credits_message"].return_value = (
            "Insufficient credits"
        )

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == 0
        assert result["user_message"] == "Insufficient credits"
        assert result["log_message"] == "Insufficient credits for test_owner/test_repo"

    def test_auto_reload_triggered_when_below_threshold(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": MAX_CREDIT_COST_USD,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == MAX_CREDIT_COST_USD
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_not_triggered_when_above_threshold(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": MAX_CREDIT_COST_USD * 3,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == MAX_CREDIT_COST_USD * 3
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_auto_reload_not_triggered_when_disabled(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": MAX_CREDIT_COST_USD,
            "auto_reload_enabled": False,
            "auto_reload_threshold_usd": 10,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == MAX_CREDIT_COST_USD
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_auto_reload_triggered_when_balance_is_zero(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 0,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }
        mock_dependencies["get_insufficient_credits_message"].return_value = (
            "Insufficient credits"
        )

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["credit_balance_usd"] == 0
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_triggered_when_balance_is_negative(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": -MAX_CREDIT_COST_USD,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }
        mock_dependencies["get_insufficient_credits_message"].return_value = (
            "Insufficient credits"
        )

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["credit_balance_usd"] == -MAX_CREDIT_COST_USD
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_triggered_at_exact_threshold(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 10,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 10
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_with_missing_threshold_defaults_to_zero(
        self, mock_dependencies
    ):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 0,
            "auto_reload_enabled": True,
        }
        mock_dependencies["get_insufficient_credits_message"].return_value = (
            "Insufficient credits"
        )

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["credit_balance_usd"] == 0
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_get_billing_type_called_with_correct_parameters(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "exception"

        check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        mock_dependencies["get_billing_type"].assert_called_once_with(
            owner_name="test_owner",
        )

    def test_all_return_fields_are_present(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "exception"

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        required_fields = [
            "can_proceed",
            "billing_type",
            "credit_balance_usd",
            "user_message",
            "log_message",
        ]
        for field in required_fields:
            assert field in result

    def test_credit_billing_with_zero_threshold_and_positive_balance(
        self, mock_dependencies
    ):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 1,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 0,
        }

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 1
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_unknown_billing_type_fallback_behavior(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "unknown_type"

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert result["can_proceed"] is False
        assert result["billing_type"] == "unknown_type"
        assert result["credit_balance_usd"] == 0
        assert result["user_message"] == ""
        assert result["log_message"] == ""

    def test_function_signature_and_return_type_structure(self, mock_dependencies):
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {"credit_balance_usd": 10}

        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            sender_name="test_sender",
        )

        assert isinstance(result, dict)
        assert isinstance(result["can_proceed"], bool)
        assert isinstance(result["billing_type"], str)
        assert isinstance(result["credit_balance_usd"], int)
        assert isinstance(result["user_message"], str)
        assert isinstance(result["log_message"], str)

    def test_credit_billing_with_edge_case_balances(self, mock_dependencies):
        test_cases = [
            (1, True, "Checked credit balance. $1 remaining."),
            (0, False, "Insufficient credits for test_owner/test_repo"),
            (-1, False, "Insufficient credits for test_owner/test_repo"),
        ]

        for balance, expected_can_proceed, expected_log_message in test_cases:
            mock_dependencies["get_billing_type"].return_value = "credit"
            mock_dependencies["get_owner"].return_value = {
                "credit_balance_usd": balance
            }
            if not expected_can_proceed:
                mock_dependencies["get_insufficient_credits_message"].return_value = (
                    "Insufficient credits"
                )

            result = check_availability(
                owner_id=123,
                owner_name="test_owner",
                repo_name="test_repo",
                sender_name="test_sender",
            )

            assert (
                result["can_proceed"] is expected_can_proceed
            ), f"Failed for balance {balance}"
            assert (
                result["credit_balance_usd"] == balance
            ), f"Failed for balance {balance}"
            assert (
                result["log_message"] == expected_log_message
            ), f"Failed for balance {balance}"

            mock_dependencies["get_insufficient_credits_message"].reset_mock()

    def test_exception_handling_returns_default_on_error(self):
        with patch(
            "services.stripe.check_availability.get_billing_type"
        ) as mock_get_billing_type:
            mock_get_billing_type.side_effect = Exception("Test exception")

            result = check_availability(
                owner_id=123,
                owner_name="test_owner",
                repo_name="test_repo",
                sender_name="test_sender",
            )

            expected_default = {
                "can_proceed": False,
                "billing_type": "credit",
                "credit_balance_usd": 0,
                "user_message": "Error checking availability",
                "log_message": "Error checking availability",
            }
            assert result == expected_default

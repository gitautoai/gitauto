from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from services.stripe.check_availability import check_availability


class TestCheckAvailability:
    """Test cases for check_availability function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch("services.stripe.check_availability.get_stripe_customer_id") as mock_get_stripe_customer_id, \
             patch("services.stripe.check_availability.get_paid_subscription") as mock_get_paid_subscription, \
             patch("services.stripe.check_availability.get_billing_type") as mock_get_billing_type, \
             patch("services.stripe.check_availability.check_subscription_limit") as mock_check_subscription_limit, \
             patch("services.stripe.check_availability.get_owner") as mock_get_owner, \
             patch("services.stripe.check_availability.trigger_auto_reload") as mock_trigger_auto_reload, \
             patch("services.stripe.check_availability.get_subscription_limit_message") as mock_get_subscription_limit_message, \
             patch("services.stripe.check_availability.get_insufficient_credits_message") as mock_get_insufficient_credits_message:

            yield {
                "get_stripe_customer_id": mock_get_stripe_customer_id,
                "get_paid_subscription": mock_get_paid_subscription,
                "get_billing_type": mock_get_billing_type,
                "check_subscription_limit": mock_check_subscription_limit,
                "get_owner": mock_get_owner,
                "trigger_auto_reload": mock_trigger_auto_reload,
                "get_subscription_limit_message": mock_get_subscription_limit_message,
                "get_insufficient_credits_message": mock_get_insufficient_credits_message,
            }

    def test_exception_billing_type_allows_unlimited_access(self, mock_dependencies):
        """Test that exception billing type allows unlimited access."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_123"
        mock_dependencies["get_paid_subscription"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "exception"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["billing_type"] == "exception"
        assert result["log_message"] == "Exception owner - unlimited access."
        assert result["user_message"] == ""
        assert result["requests_left"] is None
        assert result["credit_balance_usd"] == 0
        assert result["period_end_date"] is None

    def test_subscription_billing_type_with_available_requests(self, mock_dependencies):
        """Test subscription billing type when requests are available."""
        # Arrange
        period_end = datetime(2024, 12, 31)
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_123"
        mock_dependencies["get_paid_subscription"].return_value = {"id": "sub_123"}
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": True,
            "requests_left": 50,
            "period_end_date": period_end,
            "request_limit": 100,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["billing_type"] == "subscription"
        assert result["requests_left"] == 50
        assert result["period_end_date"] == period_end
        assert result["log_message"] == "Checked subscription limit. 50 requests left."
        assert result["user_message"] == ""
        mock_dependencies["check_subscription_limit"].assert_called_once_with(
            paid_subscription={"id": "sub_123"},
            installation_id=456,
        )

    def test_subscription_billing_type_with_no_requests_left(self, mock_dependencies):
        """Test subscription billing type when no requests are left."""
        # Arrange
        period_end = datetime(2024, 12, 31)
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_123"
        mock_dependencies["get_paid_subscription"].return_value = {"id": "sub_123"}
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": False,
            "requests_left": 0,
            "period_end_date": period_end,
            "request_limit": 100,
        }
        mock_dependencies["get_subscription_limit_message"].return_value = "Subscription limit reached"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["billing_type"] == "subscription"
        assert result["requests_left"] == 0
        assert result["period_end_date"] == period_end
        assert result["user_message"] == "Subscription limit reached"
        assert result["log_message"] == "Request limit reached for test_owner/test_repo"
        mock_dependencies["get_subscription_limit_message"].assert_called_once_with(
            user_name="test_sender",
            request_limit=100,
            period_end_date=period_end,
        )

    def test_credit_billing_type_with_sufficient_credits(self, mock_dependencies):
        """Test credit billing type with sufficient credits."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 50,
            "auto_reload_enabled": False,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == 50
        assert result["log_message"] == "Checked credit balance. $50 remaining."
        assert result["user_message"] == ""
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_credit_billing_type_with_insufficient_credits(self, mock_dependencies):
        """Test credit billing type with insufficient credits."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {"credit_balance_usd": 0}
        mock_dependencies["get_insufficient_credits_message"].return_value = "Insufficient credits"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == 0
        assert result["user_message"] == "Insufficient credits"
        assert result["log_message"] == "Insufficient credits for test_owner/test_repo"
        mock_dependencies["get_insufficient_credits_message"].assert_called_once_with(
            user_name="test_sender"
        )

    def test_credit_billing_type_with_no_owner_data(self, mock_dependencies):
        """Test credit billing type when owner data is None."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = None
        mock_dependencies["get_insufficient_credits_message"].return_value = "Insufficient credits"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["billing_type"] == "credit"
        assert result["credit_balance_usd"] == 0
        assert result["user_message"] == "Insufficient credits"
        assert result["log_message"] == "Insufficient credits for test_owner/test_repo"

    def test_auto_reload_triggered_when_below_threshold(self, mock_dependencies):
        """Test that auto-reload is triggered when credits are below threshold."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 5,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 5
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_not_triggered_when_above_threshold(self, mock_dependencies):
        """Test that auto-reload is not triggered when credits are above threshold."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 15,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 15
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_auto_reload_not_triggered_when_disabled(self, mock_dependencies):
        """Test that auto-reload is not triggered when disabled."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 5,
            "auto_reload_enabled": False,
            "auto_reload_threshold_usd": 10,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 5
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_auto_reload_not_triggered_when_insufficient_credits(self, mock_dependencies):
        """Test that auto-reload is not triggered when credits are insufficient."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 0,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }
        mock_dependencies["get_insufficient_credits_message"].return_value = "Insufficient credits"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["credit_balance_usd"] == 0
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_auto_reload_triggered_at_exact_threshold(self, mock_dependencies):
        """Test that auto-reload is triggered when credits equal the threshold."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 10,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 10,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 10
        mock_dependencies["trigger_auto_reload"].assert_called_once()

    def test_auto_reload_with_missing_threshold_defaults_to_zero(self, mock_dependencies):
        """Test that auto-reload uses default threshold of 0 when not specified."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 0,
            "auto_reload_enabled": True,
            # auto_reload_threshold_usd not specified, should default to 0
        }
        mock_dependencies["get_insufficient_credits_message"].return_value = "Insufficient credits"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["credit_balance_usd"] == 0
        # Should not trigger auto-reload because balance is 0 and threshold is 0 (not <= 0)
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_subscription_with_no_stripe_customer_id(self, mock_dependencies):
        """Test subscription billing when no stripe customer ID exists."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_paid_subscription"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": False,
            "requests_left": 0,
            "period_end_date": None,
            "request_limit": 0,
        }
        mock_dependencies["get_subscription_limit_message"].return_value = "No subscription found"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["billing_type"] == "subscription"
        mock_dependencies["get_paid_subscription"].assert_not_called()
        mock_dependencies["check_subscription_limit"].assert_called_once_with(
            paid_subscription=None,
            installation_id=456,
        )

    def test_subscription_with_stripe_customer_id_but_no_subscription(self, mock_dependencies):
        """Test subscription billing with stripe customer ID but no active subscription."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_123"
        mock_dependencies["get_paid_subscription"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": False,
            "requests_left": 0,
            "period_end_date": None,
            "request_limit": 0,
        }
        mock_dependencies["get_subscription_limit_message"].return_value = "No active subscription"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is False
        assert result["billing_type"] == "subscription"
        mock_dependencies["get_paid_subscription"].assert_called_once_with(customer_id="cus_123")
        mock_dependencies["check_subscription_limit"].assert_called_once_with(
            paid_subscription=None,
            installation_id=456,
        )

    def test_get_billing_type_called_with_correct_parameters(self, mock_dependencies):
        """Test that get_billing_type is called with correct parameters."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_123"
        mock_dependencies["get_paid_subscription"].return_value = {"id": "sub_123"}
        mock_dependencies["get_billing_type"].return_value = "exception"

        # Act
        check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        mock_dependencies["get_billing_type"].assert_called_once_with(
            owner_name="test_owner",
            stripe_customer_id="cus_123",
            paid_subscription={"id": "sub_123"},
        )

    def test_all_return_fields_are_present(self, mock_dependencies):
        """Test that all required fields are present in the return value."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "exception"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        required_fields = [
            "can_proceed",
            "billing_type",
            "requests_left",
            "credit_balance_usd",
            "period_end_date",
            "user_message",
            "log_message",
        ]
        for field in required_fields:
            assert field in result

    def test_credit_billing_with_zero_threshold_and_positive_balance(self, mock_dependencies):
        """Test auto-reload behavior when threshold is 0 and balance is positive."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {
            "credit_balance_usd": 1,
            "auto_reload_enabled": True,
            "auto_reload_threshold_usd": 0,
        }

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["credit_balance_usd"] == 1
        # Should not trigger auto-reload because balance (1) > threshold (0)
        mock_dependencies["trigger_auto_reload"].assert_not_called()

    def test_unknown_billing_type_fallback_behavior(self, mock_dependencies):
        """Test behavior when an unknown billing type is returned."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "unknown_type"

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert - should maintain default values when no billing type matches
        assert result["can_proceed"] is False
        assert result["billing_type"] == "unknown_type"
        assert result["requests_left"] is None
        assert result["credit_balance_usd"] == 0
        assert result["period_end_date"] is None
        assert result["user_message"] == ""
        assert result["log_message"] == ""

    def test_function_signature_and_return_type_structure(self, mock_dependencies):
        """Test that function signature and return structure are correct."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = None
        mock_dependencies["get_billing_type"].return_value = "credit"
        mock_dependencies["get_owner"].return_value = {"credit_balance_usd": 10}

        # Act
        result = check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert return type structure
        assert isinstance(result, dict)
        assert isinstance(result["can_proceed"], bool)
        assert isinstance(result["billing_type"], str)
        assert result["requests_left"] is None or isinstance(result["requests_left"], int)
        assert isinstance(result["credit_balance_usd"], int)
        assert result["period_end_date"] is None or isinstance(result["period_end_date"], datetime)
        assert isinstance(result["user_message"], str)
        assert isinstance(result["log_message"], str)

    def test_subscription_with_complex_subscription_limit_data(self, mock_dependencies):
        """Test subscription billing with complex subscription limit data."""
        # Arrange
        period_end = datetime(2024, 12, 31, 23, 59, 59)
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_complex123"
        mock_dependencies["get_paid_subscription"].return_value = {
            "id": "sub_complex123",
            "status": "active",
            "current_period_end": period_end.timestamp(),
        }
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": True,
            "requests_left": 999,
            "period_end_date": period_end,
            "request_limit": 1000,
        }

        # Act
        result = check_availability(
            owner_id=999,
            owner_name="complex_owner",
            repo_name="complex_repo",
            installation_id=888,
            sender_name="complex_sender",
        )

        # Assert
        assert result["can_proceed"] is True
        assert result["billing_type"] == "subscription"
        assert result["requests_left"] == 999
        assert result["period_end_date"] == period_end
        assert "999 requests left" in result["log_message"]
        assert result["user_message"] == ""

    def test_credit_billing_with_edge_case_balances(self, mock_dependencies):
        """Test credit billing with various edge case balance values."""
        test_cases = [
            (1, True, "Checked credit balance. $1 remaining."),
            (0, False, "Insufficient credits for test_owner/test_repo"),
            (-1, False, "Insufficient credits for test_owner/test_repo"),
        ]

        for balance, expected_can_proceed, expected_log_message in test_cases:
            # Arrange
            mock_dependencies["get_stripe_customer_id"].return_value = None
            mock_dependencies["get_billing_type"].return_value = "credit"
            mock_dependencies["get_owner"].return_value = {"credit_balance_usd": balance}
            if not expected_can_proceed:
                mock_dependencies["get_insufficient_credits_message"].return_value = "Insufficient credits"

            # Act
            result = check_availability(
                owner_id=123,
                owner_name="test_owner",
                repo_name="test_repo",
                installation_id=456,
                sender_name="test_sender",
            )

            # Assert
            assert result["can_proceed"] is expected_can_proceed, f"Failed for balance {balance}"
            assert result["credit_balance_usd"] == balance, f"Failed for balance {balance}"
            assert result["log_message"] == expected_log_message, f"Failed for balance {balance}"

            # Reset mocks for next iteration
            mock_dependencies["get_insufficient_credits_message"].reset_mock()

    def test_all_external_dependencies_are_called_correctly(self, mock_dependencies):
        """Test that all external dependencies are called with correct parameters."""
        # Arrange
        mock_dependencies["get_stripe_customer_id"].return_value = "cus_test"
        mock_dependencies["get_paid_subscription"].return_value = {"id": "sub_test"}
        mock_dependencies["get_billing_type"].return_value = "subscription"
        mock_dependencies["check_subscription_limit"].return_value = {
            "can_proceed": False,
            "requests_left": 0,
            "period_end_date": datetime(2024, 12, 31),
            "request_limit": 100,
        }
        mock_dependencies["get_subscription_limit_message"].return_value = "Limit reached"

        # Act
        check_availability(
            owner_id=123,
            owner_name="test_owner",
            repo_name="test_repo",
            installation_id=456,
            sender_name="test_sender",
        )

        # Assert all dependencies were called correctly
        mock_dependencies["get_stripe_customer_id"].assert_called_once_with(123)
        mock_dependencies["get_paid_subscription"].assert_called_once_with(customer_id="cus_test")
        mock_dependencies["get_billing_type"].assert_called_once_with(
            owner_name="test_owner",
            stripe_customer_id="cus_test",
            paid_subscription={"id": "sub_test"},
        )
        mock_dependencies["check_subscription_limit"].assert_called_once_with(
            paid_subscription={"id": "sub_test"},
            installation_id=456,
        )
        mock_dependencies["get_subscription_limit_message"].assert_called_once_with(
            user_name="test_sender",
            request_limit=100,
            period_end_date=datetime(2024, 12, 31),
        )

    def test_exception_handling_returns_default_on_error(self):
        """Test that exceptions are handled and default values are returned."""
        # This test verifies the decorator behavior by causing an exception
        with patch("services.stripe.check_availability.get_stripe_customer_id") as mock_get_stripe_customer_id:
            # Make the first dependency call raise an exception
            mock_get_stripe_customer_id.side_effect = Exception("Test exception")

            # Act
            result = check_availability(
                owner_id=123,
                owner_name="test_owner",
                repo_name="test_repo",
                installation_id=456,
                sender_name="test_sender",
            )

            # Assert that default values are returned
            expected_default = {
                "can_proceed": False,
                "billing_type": "credit",
                "requests_left": None,
                "credit_balance_usd": 0,
                "period_end_date": None,
                "user_message": "Error checking availability",
                "log_message": "Error checking availability",
            }
            assert result == expected_default

    @patch("services.stripe.check_availability.handle_exceptions")
    def test_function_has_exception_handling_decorator(self, mock_handle_exceptions):
        """Test that the function is decorated with handle_exceptions."""
        # This test verifies that the decorator is applied
        # The actual exception handling behavior is tested by the decorator itself
        mock_handle_exceptions.assert_called()

        # Verify the decorator configuration
        call_args = mock_handle_exceptions.call_args
        assert call_args[1]["raise_on_error"] is False

        expected_default = {
            "can_proceed": False,
            "billing_type": "credit",
            "requests_left": None,
            "credit_balance_usd": 0,
            "period_end_date": None,
            "user_message": "Error checking availability",
            "log_message": "Error checking availability",
        }
        assert call_args[1]["default_return_value"] == expected_default

# Standard imports
import unittest
from unittest.mock import patch, MagicMock

# Third-party imports
from stripe import StripeError

# Local imports
from services.stripe.create_stripe_customer import create_stripe_customer


class TestCreateStripeCustomer(unittest.TestCase):
    """Test cases for create_stripe_customer function"""

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_success(self, mock_stripe):
        """Test successful customer creation"""
        # Setup
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer

        # Execute
        result = create_stripe_customer(
            owner_id=123,
            owner_name="test-owner",
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert
        self.assertEqual(result, "cus_test123")
        mock_stripe.Customer.create.assert_called_once_with(
            name="test-owner",
            metadata={
                "owner_id": "123",
                "installation_id": "456",
                "description": "GitAuto Github App Installation Event",
                "user_id": "789",
                "user_name": "test-user",
            },
        )

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_error(self, mock_stripe):
        """Test error handling when Stripe API raises an exception"""
        # Setup
        mock_stripe.Customer.create.side_effect = Exception("Stripe API error")

        # Execute
        result = create_stripe_customer(
            owner_id=123,
            owner_name="test-owner",
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert
        self.assertIsNone(
            result
        )  # Should return None due to handle_exceptions decorator
        mock_stripe.Customer.create.assert_called_once()

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_metadata_conversion(self, mock_stripe):
        """Test that numeric values are properly converted to strings in metadata"""
        # Setup
        mock_customer = MagicMock()
        mock_customer.id = "cus_test456"
        mock_stripe.Customer.create.return_value = mock_customer

        # Execute
        create_stripe_customer(
            owner_id=123,
            owner_name="test-owner",
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert that all numeric values were converted to strings in metadata
        _, kwargs = mock_stripe.Customer.create.call_args
        self.assertEqual(kwargs["metadata"]["owner_id"], "123")
        self.assertEqual(kwargs["metadata"]["installation_id"], "456")
        self.assertEqual(kwargs["metadata"]["user_id"], "789")

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_with_empty_name(self, mock_stripe):
        """Test customer creation with empty owner name"""
        # Setup
        mock_customer = MagicMock()
        mock_customer.id = "cus_test789"
        mock_stripe.Customer.create.return_value = mock_customer

        # Execute
        result = create_stripe_customer(
            owner_id=123,
            owner_name="",  # Empty name
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert
        self.assertEqual(result, "cus_test789")
        mock_stripe.Customer.create.assert_called_once()
        # Verify empty name is passed as is
        self.assertEqual(mock_stripe.Customer.create.call_args[1]["name"], "")

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_stripe_error(self, mock_stripe):
        """Test handling of Stripe-specific errors"""
        # Setup
        mock_stripe.Customer.create.side_effect = StripeError("Stripe API error")

        # Execute
        result = create_stripe_customer(
            owner_id=123,
            owner_name="test-owner",
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert
        self.assertIsNone(
            result
        )  # Should return None due to handle_exceptions decorator

    @patch("services.stripe.create_stripe_customer.stripe")
    def test_create_stripe_customer_return_value(self, mock_stripe):
        """Test that the function returns the customer ID"""
        # Setup
        mock_customer = MagicMock()
        mock_customer.id = "cus_test_return_value"
        mock_stripe.Customer.create.return_value = mock_customer

        # Execute
        result = create_stripe_customer(
            owner_id=123,
            owner_name="test-owner",
            installation_id=456,
            user_id=789,
            user_name="test-user",
        )

        # Assert that the function returns the customer ID
        self.assertEqual(result, "cus_test_return_value")

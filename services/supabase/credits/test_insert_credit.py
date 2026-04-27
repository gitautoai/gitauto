# pylint: disable=unused-argument
# pyright: reportUnusedVariable=false, reportArgumentType=false

from unittest.mock import patch, MagicMock
import pytest
from constants.models import CREDIT_GRANT_AMOUNT_USD, GoogleModelId, MAX_CREDIT_COST_USD
from services.supabase.credits.insert_credit import insert_credit

USAGE_AMOUNT = -MAX_CREDIT_COST_USD


@pytest.fixture
def mock_supabase():
    with patch("services.supabase.credits.insert_credit.supabase") as mock:
        yield mock


@pytest.fixture
def mock_query_chain(mock_supabase):
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute

    return {
        "table": mock_table,
        "insert": mock_insert,
        "execute": mock_execute,
    }


def test_grant_inserts_correct_data(mock_supabase, mock_query_chain):
    owner_id = 123456
    result = insert_credit(
        platform="github", owner_id=owner_id, transaction_type="grant"
    )

    assert result is None
    mock_supabase.table.assert_called_once_with("credits")
    mock_query_chain["table"].insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": owner_id,
            "amount_usd": CREDIT_GRANT_AMOUNT_USD,
            "transaction_type": "grant",
        }
    )
    mock_query_chain["insert"].execute.assert_called_once()


def test_usage_inserts_correct_data_with_usage_id(mock_supabase, mock_query_chain):
    owner_id = 789012
    usage_id = 456

    with patch(
        "services.supabase.credits.insert_credit.get_credit_price",
        return_value=MAX_CREDIT_COST_USD,
    ):
        result = insert_credit(
            platform="github",
            owner_id=owner_id,
            transaction_type="usage",
            usage_id=usage_id,
        )

    assert result is None
    mock_supabase.table.assert_called_once_with("credits")
    mock_query_chain["table"].insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": owner_id,
            "amount_usd": USAGE_AMOUNT,
            "transaction_type": "usage",
            "usage_id": usage_id,
        }
    )


def test_usage_with_model_id_uses_model_specific_cost(mock_supabase, mock_query_chain):
    owner_id = 131313
    usage_id = 999
    model_id = GoogleModelId.GEMMA_4_31B

    with patch(
        "services.supabase.credits.insert_credit.get_credit_price",
        return_value=2,
    ):
        result = insert_credit(
            platform="github",
            owner_id=owner_id,
            transaction_type="usage",
            usage_id=usage_id,
            model_id=model_id,
        )

    assert result is None
    mock_query_chain["table"].insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": owner_id,
            "amount_usd": -2,
            "transaction_type": "usage",
            "usage_id": usage_id,
        }
    )


def test_none_usage_id_excluded_from_data(mock_supabase, mock_query_chain):
    owner_id = 345678
    result = insert_credit(
        platform="github", owner_id=owner_id, transaction_type="grant", usage_id=None
    )

    assert result is None
    insert_data = mock_query_chain["table"].insert.call_args[0][0]
    assert insert_data.get("usage_id", "MISSING") == "MISSING"


def test_unknown_transaction_type_returns_none(mock_supabase):
    result = insert_credit(
        platform="github", owner_id=888888, transaction_type="unknown_type"
    )
    assert result is None  # @handle_exceptions catches ValueError


def test_database_exception_returns_none(mock_supabase):
    mock_supabase.table.side_effect = Exception("Database connection error")
    result = insert_credit(platform="github", owner_id=999999, transaction_type="grant")
    assert result is None
    mock_supabase.table.assert_called_once_with("credits")


def test_insert_exception_returns_none(mock_supabase, mock_query_chain):
    mock_query_chain["table"].insert.side_effect = Exception("Insert error")

    with patch(
        "services.supabase.credits.insert_credit.get_credit_price",
        return_value=MAX_CREDIT_COST_USD,
    ):
        result = insert_credit(
            platform="github", owner_id=555555, transaction_type="usage"
        )

    assert result is None
    mock_query_chain["table"].insert.assert_called_once()


def test_execute_exception_returns_none(mock_supabase, mock_query_chain):
    mock_query_chain["insert"].execute.side_effect = Exception("Execute error")
    result = insert_credit(platform="github", owner_id=777777, transaction_type="grant")
    assert result is None
    mock_query_chain["insert"].execute.assert_called_once()


def test_attribute_error_returns_none(mock_supabase):
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    del mock_table.insert

    result = insert_credit(platform="github", owner_id=999999, transaction_type="grant")
    assert result is None


@pytest.mark.parametrize("owner_id", [0, 1, 999999999, -1])
def test_various_owner_ids(mock_supabase, mock_query_chain, owner_id):
    result = insert_credit(
        platform="github", owner_id=owner_id, transaction_type="grant"
    )

    assert result is None
    mock_query_chain["table"].insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": owner_id,
            "amount_usd": CREDIT_GRANT_AMOUNT_USD,
            "transaction_type": "grant",
        }
    )


@pytest.mark.parametrize("usage_id", [0, 1, 999999, -1])
def test_various_usage_ids(mock_supabase, mock_query_chain, usage_id):
    owner_id = 123456

    with patch(
        "services.supabase.credits.insert_credit.get_credit_price",
        return_value=MAX_CREDIT_COST_USD,
    ):
        result = insert_credit(
            platform="github",
            owner_id=owner_id,
            transaction_type="usage",
            usage_id=usage_id,
        )

    assert result is None
    mock_query_chain["table"].insert.assert_called_once_with(
        {
            "platform": "github",
            "owner_id": owner_id,
            "amount_usd": USAGE_AMOUNT,
            "transaction_type": "usage",
            "usage_id": usage_id,
        }
    )


def test_grant_uses_correct_table(mock_supabase, mock_query_chain):
    insert_credit(platform="github", owner_id=444444, transaction_type="grant")
    mock_supabase.table.assert_called_once_with("credits")

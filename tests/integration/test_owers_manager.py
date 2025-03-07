import pytest
from services.supabase.owers_manager import get_stripe_customer_id


class DummySupabaseClient:
    def __init__(self, dummy_response):
        self.dummy_response = dummy_response

    def table(self, table_name):
        return DummyTable(self.dummy_response)


class DummyTable:
    def __init__(self, dummy_response):
        self.dummy_response = dummy_response

    def select(self, fields):
        return self

    def eq(self, column, value):
        return self

    def execute(self):
        return self.dummy_response


def test_get_stripe_customer_id_no_data(monkeypatch):
    # Test when no data is returned
    dummy_response = []  # No data
    monkeypatch.setattr("services.supabase.owers_manager.supabase", DummySupabaseClient(dummy_response))
    result = get_stripe_customer_id(1)
    assert result is None


def test_get_stripe_customer_id_invalid_format(monkeypatch):
    # Test when data doesn't follow expected format: less than 2 elements
    dummy_response = [None]
    monkeypatch.setattr("services.supabase.owers_manager.supabase", DummySupabaseClient(dummy_response))
    result = get_stripe_customer_id(2)
    assert result is None


def test_get_stripe_customer_id_success(monkeypatch):
    # Test successful retrieval
    dummy_response = [None, [{"stripe_customer_id": "cus_12345"}]]
    monkeypatch.setattr("services.supabase.owers_manager.supabase", DummySupabaseClient(dummy_response))
    result = get_stripe_customer_id(3)
    assert result == "cus_12345"

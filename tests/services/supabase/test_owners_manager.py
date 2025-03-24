import pytest
from services.supabase.owners_manager import get_stripe_customer_id
from services.supabase.client import supabase


@pytest.fixture(autouse=True)
def setup_test_data():
    supabase.table("owners").upsert(
        [{"owner_id": 4620828, "stripe_customer_id": "cus_RCZOxKQHsSk93v"}]
    ).execute()
    yield
    supabase.table("owners").delete().eq("owner_id", 4620828).execute()


def test_get_stripe_customer_id_known_owner():
    result = get_stripe_customer_id(owner_id=4620828)
    assert result == "cus_RCZOxKQHsSk93v"


def test_get_stripe_customer_id_nonexistent_owner():
    result = get_stripe_customer_id(owner_id=999999)
    assert result is None


def test_get_stripe_customer_id_with_none():
    supabase.table("owners").upsert(
        [{"owner_id": 123456, "stripe_customer_id": None}]
    ).execute()
    result = get_stripe_customer_id(owner_id=123456)
    supabase.table("owners").delete().eq("owner_id", 123456).execute()
    assert result is None


def test_get_stripe_customer_id_with_invalid_type():
    with pytest.raises(Exception):
        get_stripe_customer_id(owner_id="invalid")

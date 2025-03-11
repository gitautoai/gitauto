from services.supabase.owers_manager import get_stripe_customer_id


def test_get_stripe_customer_id_success():
    owner_id = 4620828
    expected_customer_id = "cus_RCZOxKQHsSk93v"
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result == expected_customer_id


def test_get_stripe_customer_id_nonexistent():
    owner_id = 999999999
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_invalid():
    result = get_stripe_customer_id(owner_id=-1)
    assert result is None

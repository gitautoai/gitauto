from services.supabase.owers_manager import get_stripe_customer_id


def test_get_stripe_customer_id_success():
    owner_id = 4620828
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result == "cus_RCZOxKQHsSk93v"


def test_get_stripe_customer_id_non_existent():
    owner_id = 999999999
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_zero():
    owner_id = 0
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_negative():
    owner_id = -1
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None


def test_get_stripe_customer_id_invalid_type():
    owner_id = "invalid"
    result = get_stripe_customer_id(owner_id=owner_id)
    assert result is None

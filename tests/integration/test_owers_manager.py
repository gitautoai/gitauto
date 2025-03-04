def test_get_stripe_customer_id_zero_owner():
    assert get_stripe_customer_id(0) is None
def test_get_stripe_customer_id_float():
    import pytest
    with pytest.raises(Exception):
        get_stripe_customer_id(3.14)

def test_get_stripe_customer_id_none():
    import pytest
    with pytest.raises(Exception):

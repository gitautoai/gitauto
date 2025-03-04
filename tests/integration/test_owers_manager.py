def test_get_stripe_customer_id_zero_owner():
    assert get_stripe_customer_id(0) is None

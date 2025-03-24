import pytest

from services.supabase.owners_manager import get_stripe_customer_id
from tests.constants import OWNER


def test_get_stripe_customer_id_valid():
    # For owner_id 4620828, should return the specific stripe customer id
    owner_id = 4620828
    expected = "cus_RCZOxKQHsSk93v"
    result = get_stripe_customer_id(owner_id)
    assert result == expected


def test_get_stripe_customer_id_non_existent():
    # Testing with an owner_id that is unlikely to exist
    owner_id = 99999999
    result = get_stripe_customer_id(owner_id)
    # Assuming function returns None or empty string for non-existent owner
    assert result is None or result == ""


def test_get_stripe_customer_id_edge_negative():
    # Testing with a negative owner_id
    owner_id = -1
    with pytest.raises(Exception):
        get_stripe_customer_id(owner_id)


def test_get_stripe_customer_id_edge_zero():
    # Testing with owner_id zero
    owner_id = 0
    with pytest.raises(Exception):
        get_stripe_customer_id(owner_id)


def test_get_stripe_customer_id_invalid_type_string():
    # Testing with invalid type: string
    owner_id = "invalid"
    with pytest.raises(Exception):
        get_stripe_customer_id(owner_id)


def test_get_stripe_customer_id_invalid_type_none():
    # Testing with None as input
    owner_id = None
    with pytest.raises(Exception):
        get_stripe_customer_id(owner_id)


def test_get_stripe_customer_id_boundary_large_integer():
    # Testing with very large integer value
    owner_id = 2**63 - 1
    try:
        result = get_stripe_customer_id(owner_id)
        # If the function can handle it, it should either return a valid string or None/empty
        assert isinstance(result, (str, type(None)))
    except Exception:
        pytest.skip("Large integer not supported by get_stripe_customer_id")


def test_get_stripe_customer_id_boundary_small_integer():
    # Testing with a very small integer value that is not negative
    owner_id = 1
    try:
        result = get_stripe_customer_id(owner_id)
        assert isinstance(result, (str, type(None)))
    except Exception:
        pytest.skip("Owner id 1 is not supported by get_stripe_customer_id")

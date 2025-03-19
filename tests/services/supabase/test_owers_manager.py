import pytest
from services.supabase.owers_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator


@timer_decorator
@pytest.mark.asyncio
async def test_get_stripe_customer_id_works() -> None:
    wipe_installation_owner_user_data()
    
    owner_id = 4620828
    expected_customer_id = "cus_RCZOxKQHsSk93v"
    
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id == expected_customer_id


@timer_decorator
@pytest.mark.asyncio
async def test_get_stripe_customer_id_returns_none_for_nonexistent_owner() -> None:
    wipe_installation_owner_user_data()
    
    owner_id = 999999999
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id is None


@timer_decorator
@pytest.mark.asyncio
async def test_get_stripe_customer_id_returns_none_for_invalid_owner_id() -> None:
    wipe_installation_owner_user_data()
    
    owner_id = -1
    customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert customer_id is None


@timer_decorator
@pytest.mark.asyncio
async def test_get_stripe_customer_id_returns_none_for_zero_owner_id() -> None:
    wipe_installation_owner_user_data()
    assert get_stripe_customer_id(owner_id=0) is None
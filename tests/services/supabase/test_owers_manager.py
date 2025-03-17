from services.supabase.owers_manager import get_stripe_customer_id
from tests.services.supabase.wipe_data import wipe_installation_owner_user_data
from utils.timer import timer_decorator


@timer_decorator
def test_get_stripe_customer_id_known_owner():
    wipe_installation_owner_user_data()
    owner_id = 4620828
    stripe_customer_id = get_stripe_customer_id(owner_id=owner_id)
    assert stripe_customer_id == "cus_RCZOxKQHsSk93v"


@timer_decorator
def test_get_stripe_customer_id_edge_cases():
    wipe_installation_owner_user_data()
    
    # Test non-existent owner_id
    stripe_customer_id = get_stripe_customer_id(owner_id=999999999)
    assert stripe_customer_id is None

    # Test invalid owner_id (negative number)
    stripe_customer_id = get_stripe_customer_id(owner_id=-1)
    assert stripe_customer_id is None

    # Test owner without stripe_customer_id
    # Note: This assumes the database is clean after wipe_installation_owner_user_data()
    stripe_customer_id = get_stripe_customer_id(owner_id=123456)
    assert stripe_customer_id is None


if __name__ == "__main__":
    test_get_stripe_customer_id_known_owner()
    test_get_stripe_customer_id_edge_cases()
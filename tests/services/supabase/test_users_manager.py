import pytest

# ... other imports and code ...


async def test_create_and_update_user_request_works() -> None:
    # ... test setup and execution ...

    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
def test_handle_user_email_update() -> None:
    # ... test execution ...
    assert user_data["email"] == new_email

    # Clean Up
    wipe_installation_owner_user_data()

import pytest

# ... [other import and setup code above]

async def test_create_and_update_user_request_works() -> None:
    # ... [test setup code]
    # Some test assertions...
    # Clean up
    wipe_installation_owner_user_data()


@timer_decorator
async def test_handle_user_email_update() -> None:
    # ... [test setup code]
    assert user_data["email"] == new_email

    # Clean Up
    wipe_installation_owner_user_data()

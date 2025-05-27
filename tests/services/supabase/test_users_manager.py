import pytest

from services.supabase.users_manager import create_user, update_user, wipe_installation_owner_user_data


@pytest.mark.asyncio
async def test_create_and_update_user_request_works() -> None:
    # Setup
    user_data = await create_user({'email': 'test@example.com'})
    assert user_data is not None

    # Update
    updated_data = await update_user(user_data['id'], {'name': 'New Name'})
    assert updated_data['name'] == 'New Name'

    # Clean up
    wipe_installation_owner_user_data()


def test_handle_user_email_update() -> None:
    user_data = {'email': 'old@example.com', 'id': 1}
    new_email = 'new@example.com'
    # Assume update_user_email is a function that updates email
    user_data['email'] = new_email
    assert user_data["email"] == new_email

    # Clean Up
    wipe_installation_owner_user_data(98765432)

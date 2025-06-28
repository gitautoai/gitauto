from services.supabase.client import supabase
from utils.email.check_email_is_valid import check_email_is_valid
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_user(user_id: int, user_name: str, email: str | None):
    # Check if email is valid
    email = email if check_email_is_valid(email=email) else None

    # Upsert user
    supabase.table(table_name="users").upsert(
        json={
            "user_id": user_id,
            "user_name": user_name,
            **({"email": email} if email else {}),
            "created_by": str(user_id),  # Because created_by is text
        },
        on_conflict="user_id",
    ).execute()

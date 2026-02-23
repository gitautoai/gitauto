from services.supabase.client import supabase
from utils.email.check_email_is_valid import check_email_is_valid
from utils.error.handle_exceptions import handle_exceptions


# Cross-ref: website/app/actions/supabase/users/upsert-user.ts
@handle_exceptions(default_return_value=None, raise_on_error=False)
def upsert_user(user_id: int, user_name: str, email: str | None, display_name: str):
    # Check if email is valid
    email = email if check_email_is_valid(email=email) else None

    # Upsert user
    json: dict = {
        "user_id": user_id,
        "user_name": user_name,
        **({"display_name": display_name} if display_name else {}),
        **({"email": email} if email else {}),
        "created_by": f"{user_id}:{user_name}",
    }
    supabase.table(table_name="users").upsert(
        json=json, on_conflict="user_id"
    ).execute()

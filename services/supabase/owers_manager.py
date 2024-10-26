# Third Party imports
from supabase import create_client, Client

# Local imports
from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from utils.handle_exceptions import handle_exceptions

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=SUPABASE_URL, supabase_key=SUPABASE_SERVICE_ROLE_KEY
)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_stripe_customer_id(owner_id: int):
    """https://supabase.com/docs/reference/python/select"""
    data, _count = (
        supabase.table(table_name="owners")
        .select("stripe_customer_id")
        .eq(column="owner_id", value=owner_id)
        .execute()
    )
    customer_id: str | None = data[1][0]["stripe_customer_id"]
    return customer_id

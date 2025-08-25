from schemas.supabase.types import Coverages
from services.supabase.client import supabase
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_coverages(coverage_record: Coverages):
    result = supabase.table("coverages").insert(coverage_record).execute()
    return result.data

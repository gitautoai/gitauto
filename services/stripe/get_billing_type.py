from typing import Literal

from config import EXCEPTION_OWNERS
from utils.error.handle_exceptions import handle_exceptions


BillingType = Literal["exception", "credit"]

DEFAULT_BILLING_TYPE: BillingType = "credit"


@handle_exceptions(default_return_value=DEFAULT_BILLING_TYPE, raise_on_error=False)
def get_billing_type(owner_name: str) -> BillingType:
    if owner_name in EXCEPTION_OWNERS:
        return "exception"

    return "credit"

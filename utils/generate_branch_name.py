from datetime import datetime, timezone
from random import choices
from string import ascii_letters, digits

from config import ISSUE_NUMBER_FORMAT, PRODUCT_ID
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=True)
def generate_branch_name(issue_number: int | None = None):
    date = datetime.now(timezone.utc).strftime("%Y%m%d")  # like "20241224"
    time = datetime.now(timezone.utc).strftime("%H%M%S")  # like "120000" means 12:00:00
    random_str = "".join(choices(ascii_letters + digits, k=4))  # like "ABCD", "1234"

    if issue_number is not None:
        return f"{PRODUCT_ID}{ISSUE_NUMBER_FORMAT}{issue_number}-{date}-{time}-{random_str}"

    return f"{PRODUCT_ID}/setup-{date}-{time}-{random_str}"

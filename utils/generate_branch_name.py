from datetime import datetime, timezone
from random import choices
from string import ascii_letters, digits

from config import PRODUCT_ID
from constants.triggers import Trigger
from utils.error.handle_exceptions import handle_exceptions


# Keep in sync with website: app/api/github/create-coverage-issues/route.ts generateBranchName()
@handle_exceptions(default_return_value=None, raise_on_error=True)
def generate_branch_name(trigger: Trigger):
    date = datetime.now(timezone.utc).strftime("%Y%m%d")  # like "20241224"
    time = datetime.now(timezone.utc).strftime("%H%M%S")  # like "120000" means 12:00:00
    random_str = "".join(choices(ascii_letters + digits, k=4))  # like "ABCD", "1234"
    return f"{PRODUCT_ID}/{trigger}-{date}-{time}-{random_str}"

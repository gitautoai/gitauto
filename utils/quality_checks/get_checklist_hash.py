# Standard imports
import hashlib
import json

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.quality_checks.checklist import QUALITY_CHECKLIST


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_checklist_hash():
    serialized = json.dumps(QUALITY_CHECKLIST, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

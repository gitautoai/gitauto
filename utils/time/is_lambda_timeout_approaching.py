# Standard imports
import time

# Local imports
from utils.error.handle_exceptions import handle_exceptions

# AWS Lambda timeout limit is 15 minutes (900 seconds)
LAMBDA_TIMEOUT_SECONDS = 900


@handle_exceptions(default_return_value=(False, 0), raise_on_error=False)
def is_lambda_timeout_approaching(start_time: float, buffer_seconds: int = 60):
    elapsed_time = time.time() - start_time
    timeout_threshold = LAMBDA_TIMEOUT_SECONDS - buffer_seconds
    return elapsed_time > timeout_threshold, elapsed_time

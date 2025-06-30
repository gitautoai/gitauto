# Local imports
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_timeout_message(elapsed_time: float, process_name: str = "Process"):
    return f"{process_name} stopped due to Lambda timeout limit ({elapsed_time:.1f}s elapsed). Proceeding with current progress."

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.memory.is_lambda_oom_approaching import LAMBDA_MEMORY_MB


@handle_exceptions(default_return_value="", raise_on_error=False)
def get_oom_message(used_mb: float, process_name: str = "Process"):
    return f"{process_name} stopped due to memory limit ({used_mb:.0f}MB / {LAMBDA_MEMORY_MB}MB used). Proceeding with current progress."

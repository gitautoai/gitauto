# Standard imports
import platform
import resource

# Local imports
from utils.error.handle_exceptions import handle_exceptions

# Must match MemorySize in infrastructure/deploy-lambda-with-vpc-efs.yml
LAMBDA_MEMORY_MB = 2048

# macOS returns bytes, Linux returns KB
_IS_MACOS = platform.system() == "Darwin"


@handle_exceptions(default_return_value=(False, 0), raise_on_error=False)
def is_lambda_oom_approaching():
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if _IS_MACOS:
        used_mb = ru_maxrss / (1024 * 1024)
    else:
        used_mb = ru_maxrss / 1024
    threshold_mb = LAMBDA_MEMORY_MB * 0.9
    return used_mb > threshold_mb, used_mb

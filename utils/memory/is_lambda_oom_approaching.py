# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.memory.get_rss_mb import get_rss_mb

# Must match MemorySize in infrastructure/deploy-lambda-with-vpc-efs.yml
LAMBDA_MEMORY_MB = 2048


@handle_exceptions(default_return_value=(False, 0), raise_on_error=False)
def is_lambda_oom_approaching():
    used_mb = get_rss_mb()
    threshold_mb = LAMBDA_MEMORY_MB * 0.9
    return used_mb > threshold_mb, used_mb

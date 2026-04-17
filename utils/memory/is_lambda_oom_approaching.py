# Standard imports
import os

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.memory.get_rss_mb import get_rss_mb

# On Lambda, AWS sets this env var automatically from MemorySize in infrastructure/deploy-lambda.yml
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html
LAMBDA_MEMORY_MB = int(os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "4096"))

# Reserve 1.5 GB for Python (~800 MB) + mongod (~500 MB) + OS (~100 MB) so Node.js OOMs gracefully (catchable) before Lambda is killed
NODE_MAX_OLD_SPACE_SIZE_MB = LAMBDA_MEMORY_MB - 1536


@handle_exceptions(default_return_value=(False, 0), raise_on_error=False)
def is_lambda_oom_approaching():
    used_mb = get_rss_mb()
    threshold_mb = LAMBDA_MEMORY_MB * 0.9
    return used_mb > threshold_mb, used_mb

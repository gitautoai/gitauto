import os

# https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions/pr-agent-prod?subtab=envVars&tab=configure
IS_PRD = os.environ.get("ENV") == "prod"

PRODUCT_NAME = "GitAuto"

MAX_GITAUTO_COMMITS_PER_PR = 30
MAX_INFRA_RETRIES = 3
MAX_SAME_ERROR_RETRIES = 3

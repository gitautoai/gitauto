from config import get_env_var

# https://us-west-1.console.aws.amazon.com/lambda/home?region=us-west-1#/functions/pr-agent-prod?subtab=envVars&tab=configure
IS_PRD = get_env_var("ENV") == "prod"

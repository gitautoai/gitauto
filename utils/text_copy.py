import datetime


def request_limit_reached(
    user_name: str, requests_made_in_this_cycle: int, end_date: datetime.datetime
) -> str:
    """Comment text to issue when request limit is reached after issue creation or PR Trigger"""
    return f"Hello @{user_name}, you have reached your request limit of {requests_made_in_this_cycle}, your cycle will refresh on {end_date}. Consider <a href='https://gitauto.ai/#pricing'>subscribing</a> if you want more requests."


def pull_request_completed(pull_request_url: str) -> str:
    """Comment text to issue when pull request is completed"""
    return f"Pull request completed! Check it out here {pull_request_url} 🚀"

import datetime


def request_limit_reached(
    user_name: str, request_count: int, end_date: datetime.datetime
) -> str:
    """Comment text to issue when request limit is reached after issue creation or PR Trigger"""
    return f"Hello @{user_name}, you have reached your request limit of {request_count}, your cycle will refresh on {end_date}. Consider <a href='https://gitauto.ai/#pricing'>subscribing</a> if you want more requests."


def pull_request_completed(pull_request_url: str) -> str:
    """Comment text to issue when pull request is completed"""
    return f"Pull request completed! Check it out here {pull_request_url} 🚀"


def request_issue_comment(requests_left: int, end_date: datetime.datetime):
    if requests_left == 1:
        return f"\n\nYou have 1 request left in this cycle which ends {end_date}."
    return (
        f"\n\nYou have {requests_left} requests left in this cycle which ends {end_date}."
    )

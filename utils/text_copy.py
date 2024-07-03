import datetime

# Local imports
from config import PRODUCT_ID


def request_limit_reached(
    user_name: str, request_count: int, end_date: datetime.datetime
) -> str:
    """Comment text to issue when request limit is reached after issue creation or PR Trigger"""
    return f"Hello @{user_name}, you have reached your request limit of {request_count}, your cycle will refresh on {end_date}.\nConsider <a href='https://gitauto.ai/#pricing'>subscribing</a> if you want more requests.\nIf you have any questions or concerns, please contact us at [info@gitauto.ai](mailto:info@gitauto.ai)."


def pull_request_completed(issuer_name: str, sender_name: str, pr_url: str) -> str:
    """Comment text to issue when pull request is completed"""
    if sender_name == issuer_name:
        user_part = f"@{issuer_name}"
    elif sender_name == PRODUCT_ID:
        user_part = f"@{issuer_name}"
    else:
        user_part = f"@{issuer_name} and @{sender_name}"
    return f"{user_part} Pull request completed! Check it out here {pr_url} 🚀"


def request_issue_comment(requests_left: int, end_date: datetime.datetime):
    """Text Copy to be added to issue comment"""
    if requests_left == 1:
        return f"\n\nYou have 1 request left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at [info@gitauto.ai](mailto:info@gitauto.ai)."
    return f"\n\nYou have {requests_left} requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at [info@gitauto.ai](mailto:info@gitauto.ai)."


UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY = "Sorry, we have an error. Please try again.\n\nHave feedback or need help?\nFeel free to email [info@gitauto.ai](mailto:info@gitauto.ai)."
UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE = "No changes were detected. Please add more details to the issue and try again.\n\nHave feedback or need help?\n[info@gitauto.ai](mailto:info@gitauto.ai)"

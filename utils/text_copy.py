import datetime

# Local imports
from config import EMAIL_LINK, PRODUCT_ID


def request_limit_reached(
    user_name: str, request_count: int, end_date: datetime.datetime
) -> str:
    """Comment text to issue when request limit is reached after issue creation or PR Trigger"""
    return f"Hello @{user_name}, you have reached your request limit of {request_count}, your cycle will refresh on {end_date}.\nConsider <a href='https://gitauto.ai/#pricing'>subscribing</a> if you want more requests.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."


def pull_request_completed(
    issuer_name: str, sender_name: str, pr_url: str, is_automation: bool
) -> str:
    """Comment text to issue when pull request is completed"""
    # Ex) sentry-io[bot] is the issuer and gitauto-ai[bot] is the sender
    if "[bot]" in issuer_name and ("[bot]" in sender_name or PRODUCT_ID in sender_name):
        user_part = ""

    # Ex1) A user is the issuer and sender
    # Ex2) sender_name contains gitauto
    elif issuer_name == sender_name or PRODUCT_ID in sender_name:
        user_part = f"@{issuer_name} "

    # Ex) A user is the issuer and another user is the sender
    else:
        user_part = f"@{issuer_name} @{sender_name} "

    # For user triggers
    if not is_automation:
        return f"{user_part}Pull request completed! Check it out here {pr_url} 🚀"

    # For automation triggers
    return f"{user_part}Pull request completed! Check it out here {pr_url} 🚀\n\nNote: I automatically create a pull request for an unassigned and open issue in order from oldest to newest once a day at 00:00 UTC, as long as you have remaining automation usage. Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK}."


def request_issue_comment(requests_left: int, end_date: datetime.datetime):
    """Text Copy to be added to issue comment"""
    if requests_left == 1:
        return f"\n\nYou have 1 request left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."
    return f"\n\nYou have {requests_left} requests left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."


UPDATE_COMMENT_FOR_RAISED_ERRORS_BODY = f"Sorry, we have an error. Please try again.\n\nHave feedback or need help?\nFeel free to email {EMAIL_LINK}."
UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE = f"No changes were detected. Please add more details to the issue and try again.\n\nHave feedback or need help?\n{EMAIL_LINK}"

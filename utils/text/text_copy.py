from datetime import datetime

# Local imports
from config import EMAIL_LINK, PRODUCT_ID
from constants.messages import COMPLETED_PR
from constants.urls import DASHBOARD_CREDITS_URL, SETTINGS_TRIGGERS_URL


# Keep in sync with website: app/api/github/create-coverage-issues/route.ts gitCommand()
def git_command(new_branch_name: str) -> str:
    return (
        f"\n\n## Test these changes locally\n\n"
        f"```\n"
        f"git fetch origin\n"
        f"git checkout {new_branch_name}\n"
        f"git pull origin {new_branch_name}\n"
        f"```"
    )


def pull_request_completed(
    pr_creator: str, sender_name: str, is_automation: bool
) -> str:
    # Ex) sentry-io[bot] is the creator and gitauto-ai[bot] is the sender
    if "[bot]" in pr_creator and ("[bot]" in sender_name or PRODUCT_ID in sender_name):
        user_part = ""

    elif "[bot]" in pr_creator and (
        "[bot]" not in sender_name and PRODUCT_ID not in sender_name
    ):
        user_part = f"@{sender_name} "

    # Ex1) A user is the creator and sender
    # Ex2) sender_name contains gitauto
    elif pr_creator == sender_name or PRODUCT_ID in sender_name:
        user_part = f"@{pr_creator} "

    # Ex) A user is the creator and another user is the sender
    else:
        user_part = f"@{pr_creator} @{sender_name} "

    # For user triggers
    if not is_automation:
        return f"{user_part}{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    # For automation triggers
    return f"{user_part}{COMPLETED_PR}\n\nNote: I automatically create pull requests on a schedule. You can manage your schedule [here]({SETTINGS_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."


def request_pr_comment(
    requests_left: int,
    sender_name: str,
    end_date: datetime,
    is_credit_user: bool = False,
    credit_balance_usd: int = 0,
):
    if is_credit_user:
        return f"\n\n@{sender_name}, You have ${credit_balance_usd} in credits remaining. [View credits]({DASHBOARD_CREDITS_URL})\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."

    requests_left = 0 if requests_left < 0 else requests_left
    plural = "" if requests_left == 1 else "s"
    return f"\n\n@{sender_name}, You have {requests_left} request{plural} left in this cycle which refreshes on {end_date}.\nIf you have any questions or concerns, please contact us at {EMAIL_LINK}."


UPDATE_COMMENT_FOR_422 = f"Hey, I'm a bit lost here! Not sure which file I should be fixing. Could you give me a bit more to go on? Maybe add some details to the PR or drop a comment with some extra hints? Thanks!\n\nHave feedback or need help?\nFeel free to email {EMAIL_LINK}."
UPDATE_COMMENT_FOR_RAISED_ERRORS_NO_CHANGES_MADE = f"No changes were detected. Please add more details to the PR and try again.\n\nHave feedback or need help?\n{EMAIL_LINK}"

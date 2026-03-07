from datetime import datetime

# Local imports
from config import EMAIL_LINK
from constants.urls import DASHBOARD_CREDITS_URL


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

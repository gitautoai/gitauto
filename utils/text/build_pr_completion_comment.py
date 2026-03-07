from config import EMAIL_LINK, PRODUCT_ID
from constants.messages import COMPLETED_PR
from constants.triggers import Trigger
from constants.urls import SETTINGS_TRIGGERS_URL


def build_pr_completion_comment(
    pr_creator: str, sender_name: str, trigger: Trigger
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

    if trigger == "schedule":
        return f"{user_part}{COMPLETED_PR}\n\nI autonomously open pull requests on a schedule. You can manage your schedule [here]({SETTINGS_TRIGGERS_URL}). Should you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

    # For user triggers
    return f"{user_part}{COMPLETED_PR}\nShould you have any questions or wish to change settings or limits, please feel free to contact {EMAIL_LINK} or invite us to Slack Connect."

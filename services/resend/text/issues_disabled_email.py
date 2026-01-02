from config import PRODUCT_NAME
from constants.urls import SETTINGS_TRIGGERS_URL
from services.resend.constants import EMAIL_SIGNATURE


def get_issues_disabled_email_text(user_name: str | None, owner: str, repo: str):
    subject = "Enable Issues to use GitAuto"

    text = f"""Hi {user_name},

{PRODUCT_NAME} couldn't run on {owner}/{repo} because GitHub Issues are disabled. To continue:

1. Enable GitHub Issues: https://github.com/{owner}/{repo}/settings
2. Re-enable {PRODUCT_NAME} schedule: {SETTINGS_TRIGGERS_URL}

{EMAIL_SIGNATURE}"""

    return subject, text

from constants.urls import DASHBOARD_CREDITS_URL
from services.resend.constants import EMAIL_SIGNATURE


def get_no_credits_email_text(user_name):
    subject = "Add credits to continue"

    text = f"""Hi {user_name},

Looks like you're trying to use GitAuto but you're out of credits.

Add some credits to keep going: {DASHBOARD_CREDITS_URL}

{EMAIL_SIGNATURE}"""

    return subject, text

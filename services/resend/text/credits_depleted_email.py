from constants.urls import DASHBOARD_CREDITS_URL
from services.resend.constants import EMAIL_SIGNATURE


def get_credits_depleted_email_text(user_name):
    subject = "You're out of credits!"

    text = f"""Hey {user_name}!

Just used your last GitAuto credits on that PR. Nice work!

Grab more credits here: {DASHBOARD_CREDITS_URL}

{EMAIL_SIGNATURE}"""

    return subject, text

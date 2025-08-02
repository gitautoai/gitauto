from services.resend.constants import EMAIL_SIGNATURE


def get_suspend_email_text(user_name: str) -> tuple[str, str]:
    subject = "Taking a break from GitAuto?"

    text = f"""Hi {user_name},

I noticed you suspended GitAuto. What happened?

Any feedback? Just hit reply and let me know.

{EMAIL_SIGNATURE}"""

    return subject, text

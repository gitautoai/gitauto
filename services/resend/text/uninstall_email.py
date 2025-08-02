from services.resend.constants import EMAIL_SIGNATURE


def get_uninstall_email_text(user_name: str) -> tuple[str, str]:
    subject = "Sorry to see you go"

    text = f"""Hi {user_name},

I noticed you uninstalled GitAuto. What went wrong?

Your feedback would really help us improve - just reply to this email.

Thanks for trying GitAuto.

{EMAIL_SIGNATURE}"""

    return subject, text

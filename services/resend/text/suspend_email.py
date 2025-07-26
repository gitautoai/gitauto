def get_suspend_email_text(user_name: str) -> tuple[str, str]:
    subject = "GitAuto suspended"

    text = f"""Hi {user_name},

You suspended GitAuto. We'll be here when you're ready to come back.

Any feedback on what could be better? Just reply to this email.

Wes"""

    return subject, text

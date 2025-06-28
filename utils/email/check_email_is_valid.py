from config import GITHUB_NOREPLY_EMAIL_DOMAIN


def check_email_is_valid(email: str | None) -> bool:
    if email is None:
        return False
    if "@" not in email or "." not in email:
        return False
    if str(email).lower().endswith(GITHUB_NOREPLY_EMAIL_DOMAIN):
        return False
    return True

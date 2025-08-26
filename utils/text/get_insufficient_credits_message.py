from config import EMAIL_LINK
from constants.urls import DASHBOARD_CREDITS_URL, CONTACT_URL


def get_insufficient_credits_message(user_name: str):
    return f"Hello @{user_name}, you have insufficient credits to process this request.\n<a href='{DASHBOARD_CREDITS_URL}'>Add credits</a> to continue using GitAuto.\nIf you have any questions or concerns, <a href='{CONTACT_URL}'>visit our contact page</a> or email us at {EMAIL_LINK}."

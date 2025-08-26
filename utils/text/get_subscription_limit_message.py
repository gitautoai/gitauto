from datetime import datetime
from config import EMAIL_LINK
from constants.urls import PRODUCT_URL, PRICING_URL, CONTACT_URL


def get_subscription_limit_message(
    user_name: str, request_limit: int, period_end_date: datetime
):
    return f"Hello @{user_name}, you have reached your request limit of {request_limit}, your cycle will refresh on {period_end_date}.\n\nTo upgrade your subscription:\n1. Go to our <a href='{PRODUCT_URL}'>homepage</a>\n2. Visit the <a href='{PRICING_URL}'>pricing page</a>\n3. Access your customer portal and upgrade your quantity\n\nIf you have any questions or concerns, <a href='{CONTACT_URL}'>visit our contact page</a> or email us at {EMAIL_LINK}."

from config import EMAIL_LINK
from constants.urls import (
    CONTACT_URL,
    DASHBOARD_COVERAGE_URL,
    SETTINGS_RULES_URL,
    SETTINGS_TRIGGERS_URL,
)

CLICK_THE_CHECKBOX = "Click the checkbox below to generate a PR!"
COMPLETED_PR = "Pull request completed! Check it out here "

SETTINGS_LINKS = f"You can [turn off triggers]({SETTINGS_TRIGGERS_URL}), [update coding rules]({SETTINGS_RULES_URL}), or [exclude files]({DASHBOARD_COVERAGE_URL}).\nFor contact, email us at {EMAIL_LINK} or visit [our contact page]({CONTACT_URL})"

PERMISSION_DENIED_MESSAGE = (
    "Approve permission(s) to allow GitAuto to access the check run logs here:"
)
CHECK_RUN_STUMBLED_MESSAGE = "Oops! Check run stumbled."

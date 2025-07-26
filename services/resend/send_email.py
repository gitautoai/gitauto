# Standard imports
from datetime import datetime, timedelta, timezone
import random
import uuid

# Third party imports
import resend

# Local imports
from config import RESEND_API_KEY, EMAIL_FROM
from utils.error.handle_exceptions import handle_exceptions


resend.api_key = RESEND_API_KEY


@handle_exceptions(default_return_value=None, raise_on_error=False)
def send_email(to: str, subject: str, text: str):
    """https://resend.com/docs/api-reference/emails/send-email"""
    delay_minutes = random.randint(30, 60)  # 30 min - 1 hour
    scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

    params: resend.Emails.SendParams = {
        "from": EMAIL_FROM,
        "to": to,
        "subject": subject,
        "text": text,
        "scheduled_at": scheduled_at.isoformat() + "Z",
    }

    options: resend.Emails.SendOptions = {"idempotency_key": str(uuid.uuid4())}

    result = resend.Emails.send(params, options)
    return result

from services.aws.delete_scheduler import delete_scheduler
from services.aws.get_schedulers import get_schedulers_by_owner_id
from services.github.types.github_types import InstallationPayload
from services.resend.get_first_name import get_first_name
from services.resend.send_email import send_email
from services.resend.text.suspend_email import get_suspend_email_text
from services.resend.text.uninstall_email import get_uninstall_email_text
from services.slack.slack_notify import slack_notify
from services.supabase.email_sends.insert_email_send import insert_email_send
from services.supabase.email_sends.update_email_send import update_email_send
from services.supabase.installations.delete_installation import delete_installation
from services.supabase.users.get_user import get_user
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(raise_on_error=False)
def handle_installation_deleted_or_suspended(payload: InstallationPayload, action: str):
    owner_id = payload["installation"]["account"]["id"]
    owner_name = payload["installation"]["account"]["login"]
    sender_id = payload["sender"]["id"]
    sender_name = payload["sender"]["login"]

    verb = "deleted" if action == "deleted" else "suspended"
    slack_notify(f":skull: Installation {verb} by `{sender_name}` for `{owner_name}`")

    delete_installation(
        installation_id=payload["installation"]["id"],
        user_id=sender_id,
        user_name=sender_name,
    )

    # Send email (deduplicated per sender)
    email_type = "uninstall" if action == "deleted" else "suspend"
    get_email_text = (
        get_uninstall_email_text if action == "deleted" else get_suspend_email_text
    )
    is_new = insert_email_send(
        owner_id=sender_id, owner_name=sender_name, email_type=email_type
    )
    if is_new is not False:
        user = get_user(sender_id)
        email = user.get("email") if user else None
        display_name = (
            (
                user.get("display_name_override")
                or user.get("display_name")
                or user.get("user_name", "")
            )
            if user
            else ""
        )
        if email:
            first_name = get_first_name(display_name)
            subject, text = get_email_text(first_name)
            result = send_email(to=email, subject=subject, text=text)
            if result and result.get("id"):
                update_email_send(
                    owner_id=sender_id,
                    email_type=email_type,
                    resend_email_id=result["id"],
                )

    # Delete AWS schedulers for this owner
    schedulers_to_delete = get_schedulers_by_owner_id(owner_id)
    for schedule_name in schedulers_to_delete:
        delete_scheduler(schedule_name)

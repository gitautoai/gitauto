from postgrest.exceptions import APIError

from services.supabase.client import supabase
from services.types.base_args import Platform
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def insert_webhook_delivery(*, platform: Platform, delivery_id: str, event_name: str):
    try:
        result = (
            supabase.table("webhook_deliveries")
            .insert(
                {
                    "platform": platform,
                    "delivery_id": delivery_id,
                    "event_name": event_name,
                }
            )
            .execute()
        )

        if result.data and len(result.data) > 0:
            logger.info(
                "insert_webhook_delivery: %s/%s/%s inserted",
                platform,
                event_name,
                delivery_id,
            )
            return True

        logger.info(
            "insert_webhook_delivery: %s/%s/%s no data returned (duplicate)",
            platform,
            event_name,
            delivery_id,
        )
        return False
    except APIError as e:
        if e.code == "23505":
            logger.info(
                "insert_webhook_delivery: %s/%s/%s duplicate (23505)",
                platform,
                event_name,
                delivery_id,
            )
            return False
        logger.warning(
            "insert_webhook_delivery: %s/%s/%s APIError code=%s, re-raising",
            platform,
            event_name,
            delivery_id,
            e.code,
        )
        raise

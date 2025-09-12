import requests

from config import TIMEOUT
from constants.urls import BASE_URL
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def trigger_auto_reload():
    # https://gitauto.ai/api/cron/auto-reload

    requests.get(
        url=f"{BASE_URL}/api/cron/auto-reload",
        headers={"User-Agent": "vercel-cron/1.0"},
        timeout=TIMEOUT,
    )

from unittest.mock import Mock, patch

from config import TIMEOUT
from services.vercel.trigger_auto_reload import trigger_auto_reload


@patch("services.vercel.trigger_auto_reload.requests.get")
def test_trigger_auto_reload_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    trigger_auto_reload()

    mock_get.assert_called_once_with(
        url="https://gitauto.ai/api/cron/auto-reload",
        headers={"User-Agent": "vercel-cron/1.0"},
        timeout=TIMEOUT,
    )


@patch("services.vercel.trigger_auto_reload.requests.get")
def test_trigger_auto_reload_with_exception(mock_get):
    mock_get.side_effect = Exception("Network error")

    result = trigger_auto_reload()

    assert result is None

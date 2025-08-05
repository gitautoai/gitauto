import pytest
from urllib.parse import quote

from services.webhook.screenshot_handler import (
    get_url_filename,
    handle_screenshot_comparison,
)


class TestGetUrlFilename:
    """Test cases for get_url_filename function."""

    def test_get_url_filename_with_http_url(self):
        """Test URL filename generation for HTTP URLs."""
        url = "http://example.com/path/to/page"
        result = get_url_filename(url)
        expected = f"{quote('path/to/page')}.png"
        assert result == expected

    def test_get_url_filename_with_empty_path(self):
        """Test URL filename generation for empty paths."""
        url = "https://example.com/"
        result = get_url_filename(url)
        expected = f"{quote('index')}.png"
        assert result == expected


class TestHandleScreenshotComparison:
    """Test cases for handle_screenshot_comparison function."""

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_early_return_disabled(self):
        """Test that function returns early when feature is disabled."""
        payload = {"pull_request": {"user": {"login": "test"}}}
        result = await handle_screenshot_comparison(payload)
        assert result is None
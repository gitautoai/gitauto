import pytest
from urllib.parse import quote
import os
from unittest.mock import patch, MagicMock

from services.webhook.screenshot_handler import (
    get_url_filename,
    get_target_paths,
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

    def test_get_url_filename_with_https_url(self):
        """Test URL filename generation for HTTPS URLs."""
        url = "https://example.com/path/to/page"
        result = get_url_filename(url)
        expected = f"{quote('path/to/page')}.png"
        assert result == expected

    def test_get_url_filename_with_empty_path(self):
        """Test URL filename generation for empty paths."""
        url = "https://example.com/"
        result = get_url_filename(url)
        expected = f"{quote('index')}.png"
        assert result == expected

    def test_get_url_filename_with_root_path(self):
        """Test URL filename generation for root path."""
        path = "/"
        result = get_url_filename(path)
        expected = f"{quote('index')}.png"
        assert result == expected

    def test_get_url_filename_with_special_characters(self):
        """Test URL filename generation with special characters."""
        url = "https://example.com/path with spaces/special@chars"
        result = get_url_filename(url)
        expected = f"{quote('path with spaces/special@chars')}.png"
        assert result == expected

    def test_get_url_filename_with_query_parameters(self):
        """Test URL filename generation with query parameters."""
        url = "https://example.com/page?param=value&other=test"
        result = get_url_filename(url)
        expected = f"{quote('page')}.png"
        assert result == expected

    def test_get_url_filename_with_fragment(self):
        """Test URL filename generation with URL fragment."""
        url = "https://example.com/page#section"
        result = get_url_filename(url)
        expected = f"{quote('page')}.png"
        assert result == expected


class TestGetTargetPaths:
    """Test cases for get_target_paths function."""

    def test_get_target_paths_with_html_files(self):
        """Test getting target paths for HTML files."""
        file_changes = [
            {"filename": "index.html"},
            {"filename": "about.html"},
            {"filename": "pages/contact.html"},
        ]
        
        result = get_target_paths(file_changes, repo_dir=None)
        
        expected = ["/", "/about", "/pages/contact"]
        assert sorted(result) == sorted(expected)

    def test_get_target_paths_with_nextjs_app_router(self):
        """Test getting target paths for Next.js App Router files."""
        file_changes = [
            {"filename": "app/page.tsx"},
            {"filename": "app/about/page.jsx"},
            {"filename": "app/blog/post/page.tsx"},
        ]
        
        result = get_target_paths(file_changes, repo_dir=None)
        
        expected = ["/", "/about", "/blog/post"]
        assert sorted(result) == sorted(expected)

    def test_get_target_paths_with_nextjs_pages_router(self):
        """Test getting target paths for Next.js Pages Router files."""
        file_changes = [
            {"filename": "pages/index.tsx"},
            {"filename": "pages/about.jsx"},
            {"filename": "pages/blog/post.tsx"},
        ]
        
        result = get_target_paths(file_changes, repo_dir=None)
        
        expected = ["/", "/about", "/blog/post"]
        assert sorted(result) == sorted(expected)

    def test_get_target_paths_no_matching_files(self):
        """Test getting target paths when no files match."""
        file_changes = [
            {"filename": "components/header.tsx"},
            {"filename": "utils/helper.js"},
            {"filename": "README.md"},
        ]
        
        result = get_target_paths(file_changes, repo_dir=None)
        
        assert result == []

    def test_get_target_paths_empty_file_changes(self):
        """Test getting target paths with empty file changes."""
        file_changes = []
        
        result = get_target_paths(file_changes)
        
        assert result == []


class TestHandleScreenshotComparison:
    """Test cases for handle_screenshot_comparison function."""

    @pytest.mark.asyncio
    @patch('services.webhook.screenshot_handler.GITHUB_APP_USER_NAME', 'test-bot')
    async def test_handle_screenshot_comparison_early_return_disabled(self):
        """Test that function returns early when feature is disabled."""
        payload = {"pull_request": {"user": {"login": "test-user"}}}
        result = await handle_screenshot_comparison(payload)
        assert result is None
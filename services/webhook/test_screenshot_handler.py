# Standard imports
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock, call

# Third party imports
import pytest

# Local imports
from services.webhook.screenshot_handler import (
    get_url_filename,
    capture_screenshots,
    upload_to_s3,
    find_all_html_pages,
    get_target_paths,
    handle_screenshot_comparison,
)


class TestGetUrlFilename:
    """Test cases for get_url_filename function."""

    def test_get_url_filename_with_http_url(self):
        """Test URL filename generation with HTTP URL."""
        url = "http://example.com/path/to/page"
        result = get_url_filename(url)
        assert result == "path/to/page.png"

    def test_get_url_filename_with_https_url(self):
        """Test URL filename generation with HTTPS URL."""
        url = "https://example.com/path/to/page"
        result = get_url_filename(url)
        assert result == "path/to/page.png"

    def test_get_url_filename_with_path_only(self):
        """Test URL filename generation with path only."""
        path = "/path/to/page"
        result = get_url_filename(path)
        assert result == "path/to/page.png"

    def test_get_url_filename_with_empty_path(self):
        """Test URL filename generation with empty path."""
        url = "https://example.com/"
        result = get_url_filename(url)
        assert result == "index.png"

    def test_get_url_filename_with_root_path(self):
        """Test URL filename generation with root path."""
        path = "/"
        result = get_url_filename(path)
        assert result == "index.png"

    def test_get_url_filename_with_special_characters(self):
        """Test URL filename generation with special characters."""
        url = "https://example.com/path with spaces/page?query=1"
        result = get_url_filename(url)
        assert result == "path%20with%20spaces/page.png"

    def test_get_url_filename_with_empty_string(self):
        """Test URL filename generation with empty string."""
        result = get_url_filename("")
        assert result == "index.png"


class TestCaptureScreenshots:
    """Test cases for capture_screenshots function."""

    @pytest.fixture
    def mock_playwright(self):
        """Fixture to mock playwright."""
        with patch("services.webhook.screenshot_handler.async_playwright") as mock:
            yield mock

    @pytest.fixture
    def mock_os_makedirs(self):
        """Fixture to mock os.makedirs."""
        with patch("services.webhook.screenshot_handler.os.makedirs") as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_capture_screenshots_success(self, mock_playwright, mock_os_makedirs):
        """Test successful screenshot capture."""
        # Setup
        urls = ["http://localhost:3000/page1", "http://localhost:3000/page2"]
        output_dir = "/tmp/screenshots"
        
        # Mock playwright objects
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Execute
        result = await capture_screenshots(urls, output_dir)

        # Assert
        assert result is None
        mock_os_makedirs.assert_called_once_with(output_dir, exist_ok=True)
        mock_browser.new_context.assert_called_once()
        mock_context.new_page.assert_called_once()
        mock_page.set_viewport_size.assert_called_once_with({"width": 1512, "height": 982})
        assert mock_page.goto.call_count == 2
        assert mock_page.screenshot.call_count == 2
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_screenshots_empty_urls(self, mock_playwright, mock_os_makedirs):
        """Test screenshot capture with empty URL list."""
        # Setup
        urls = []
        output_dir = "/tmp/screenshots"
        
        # Mock playwright objects
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Execute
        result = await capture_screenshots(urls, output_dir)

        # Assert
        assert result is None
        mock_os_makedirs.assert_called_once_with(output_dir, exist_ok=True)
        mock_page.goto.assert_not_called()
        mock_page.screenshot.assert_not_called()


class TestUploadToS3:
    """Test cases for upload_to_s3 function."""

    @pytest.fixture
    def mock_boto3_client(self):
        """Fixture to mock boto3.client."""
        with patch("services.webhook.screenshot_handler.boto3.client") as mock:
            yield mock

    @pytest.fixture
    def mock_os_getenv(self):
        """Fixture to mock os.getenv."""
        with patch("services.webhook.screenshot_handler.os.getenv") as mock:
            yield mock

    def test_upload_to_s3_success(self, mock_boto3_client, mock_os_getenv):
        """Test successful S3 upload."""
        # Setup
        file_path = "/tmp/test.png"
        s3_key = "screenshots/test.png"
        bucket_name = "test-bucket"
        
        mock_os_getenv.return_value = bucket_name
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        # Execute
        result = upload_to_s3(file_path, s3_key)

        # Assert
        expected_url = f"https://{bucket_name}.s3.us-west-1.amazonaws.com/screenshots/test.png"
        assert result == expected_url
        mock_s3_client.upload_file.assert_called_once_with(
            file_path, bucket_name, s3_key, ExtraArgs={"ContentType": "image/png"}
        )

    def test_upload_to_s3_missing_bucket_name(self, mock_boto3_client, mock_os_getenv):
        """Test S3 upload when bucket name is not set."""
        # Setup
        file_path = "/tmp/test.png"
        s3_key = "screenshots/test.png"
        
        mock_os_getenv.return_value = None
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        # Execute & Assert
        with pytest.raises(ValueError, match="AWS_S3_BUCKET_NAME is not set"):
            upload_to_s3(file_path, s3_key)


class TestFindAllHtmlPages:
    """Test cases for find_all_html_pages function."""

    def test_find_all_html_pages_with_html_files(self):
        """Test finding HTML pages with HTML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            os.makedirs(os.path.join(temp_dir, "subdir"))
            
            # Create HTML files
            open(os.path.join(temp_dir, "index.html"), "w").close()
            open(os.path.join(temp_dir, "about.html"), "w").close()
            open(os.path.join(temp_dir, "subdir", "page.html"), "w").close()

            # Execute
            result = find_all_html_pages(temp_dir)

            # Assert
            assert "/" in result  # index.html -> /
            assert "/about.html" in result
            assert "/subdir/page.html" in result

    def test_find_all_html_pages_with_nextjs_app_router(self):
        """Test finding HTML pages with Next.js App Router files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Next.js App Router structure
            app_dir = os.path.join(temp_dir, "app")
            os.makedirs(os.path.join(app_dir, "about"))
            os.makedirs(os.path.join(app_dir, "products", "category"))
            
            # Create page files
            open(os.path.join(app_dir, "page.tsx"), "w").close()
            open(os.path.join(app_dir, "about", "page.tsx"), "w").close()
            open(os.path.join(app_dir, "products", "category", "page.jsx"), "w").close()
            open(os.path.join(app_dir, "layout.tsx"), "w").close()

            # Execute
            result = find_all_html_pages(temp_dir)

            # Assert
            assert "/" in result  # app/page.tsx -> /
            assert "/about" in result
            assert "/products/category" in result

    def test_find_all_html_pages_with_nextjs_pages_router(self):
        """Test finding HTML pages with Next.js Pages Router files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Next.js Pages Router structure
            pages_dir = os.path.join(temp_dir, "pages")
            os.makedirs(os.path.join(pages_dir, "api"))
            os.makedirs(os.path.join(pages_dir, "products"))
            
            # Create page files
            open(os.path.join(pages_dir, "index.tsx"), "w").close()
            open(os.path.join(pages_dir, "about.tsx"), "w").close()
            open(os.path.join(pages_dir, "products", "index.jsx"), "w").close()
            open(os.path.join(pages_dir, "contact.jsx"), "w").close()

            # Execute
            result = find_all_html_pages(temp_dir)

            # Assert
            assert "/" in result  # pages/index.tsx -> /
            assert "/about" in result
            assert "/products" in result  # pages/products/index.jsx -> /products
            assert "/contact" in result

    def test_find_all_html_pages_empty_directory(self):
        """Test finding HTML pages in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Execute
            result = find_all_html_pages(temp_dir)

            # Assert
            assert result == []


class TestGetTargetPaths:
    """Test cases for get_target_paths function."""

    def test_get_target_paths_with_css_changes(self):
        """Test getting target paths when CSS files are changed."""
        # Setup
        file_changes = [
            {"filename": "styles.css"},
            {"filename": "components/Button.tsx"},
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test HTML file
            open(os.path.join(temp_dir, "index.html"), "w").close()
            
            # Execute
            with patch("services.webhook.screenshot_handler.find_all_html_pages") as mock_find:
                mock_find.return_value = ["/", "/about"]
                result = get_target_paths(file_changes, temp_dir)

            # Assert
            assert result == ["/", "/about"]
            mock_find.assert_called_once_with(temp_dir)

    def test_get_target_paths_with_html_changes(self):
        """Test getting target paths when HTML files are changed."""
        # Setup
        file_changes = [
            {"filename": "index.html"},
            {"filename": "about.html"},
            {"filename": "contact/index.html"},
        ]
        
        # Execute
        result = get_target_paths(file_changes)

        # Assert
        expected = ["/", "/about.html", "/contact"]
        assert all(path in result for path in expected)

    def test_get_target_paths_with_nextjs_app_router(self):
        """Test getting target paths with Next.js App Router changes."""
        # Setup
        file_changes = [
            {"filename": "app/page.tsx"},
            {"filename": "app/about/page.jsx"},
            {"filename": "app/products/category/page.tsx"},
        ]
        
        # Execute
        result = get_target_paths(file_changes)

        # Assert
        expected = ["/", "/about", "/products/category"]
        assert all(path in result for path in expected)

    def test_get_target_paths_with_nextjs_pages_router(self):
        """Test getting target paths with Next.js Pages Router changes."""
        # Setup
        file_changes = [
            {"filename": "pages/index.tsx"},
            {"filename": "pages/about.jsx"},
            {"filename": "pages/products/category.tsx"},
        ]
        
        # Execute
        result = get_target_paths(file_changes)

        # Assert
        expected = ["/", "/about", "/products/category"]
        assert all(path in result for path in expected)

    def test_get_target_paths_no_relevant_changes(self):
        """Test getting target paths when no relevant files are changed."""
        # Setup
        file_changes = [
            {"filename": "README.md"},
            {"filename": "package.json"},
            {"filename": "src/utils/helper.ts"},
        ]
        
        # Execute
        result = get_target_paths(file_changes)

        # Assert
        assert result == []

    def test_get_target_paths_empty_file_changes(self):
        """Test getting target paths with empty file changes."""
        # Setup
        file_changes = []
        
        # Execute
        result = get_target_paths(file_changes)

        # Assert
        assert result == []


class TestHandleScreenshotComparison:
    """Test cases for handle_screenshot_comparison function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Fixture to mock all dependencies for handle_screenshot_comparison."""
        with patch.multiple(
            "services.webhook.screenshot_handler",
            get_installation_access_token=MagicMock(return_value="test-token"),
            get_pull_request_file_changes=MagicMock(return_value=[]),
            get_all_comments=MagicMock(return_value=[]),
            delete_comment=MagicMock(),
            create_comment=MagicMock(),
            clone_repo=MagicMock(),
            fetch_branch=MagicMock(),
            switch_to_branch=MagicMock(),
            get_current_branch=MagicMock(),
            start_local_server=MagicMock(),
            capture_screenshots=AsyncMock(),
            upload_to_s3=MagicMock(return_value="https://example.com/image.png"),
            get_target_paths=MagicMock(return_value=[]),
            os=MagicMock(),
            shutil=MagicMock(),
            sleep=MagicMock(),
        ) as mocks:
            yield mocks

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_feature_disabled(self, mock_dependencies):
        """Test that function returns early when feature is disabled."""
        # Setup
        payload = {"pull_request": {"user": {"login": "gitauto-for-dev[bot]"}}}
        
        # Execute
        result = await handle_screenshot_comparison(payload)

        # Assert
        assert result is None
        # Verify no other functions were called since it returns early
        mock_dependencies["get_installation_access_token"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_wrong_user(self, mock_dependencies):
        """Test that function returns early when PR author is not GitAuto."""
        # Setup
        payload = {
            "pull_request": {"user": {"login": "some-other-user"}},
            "repository": {"owner": {"login": "owner"}, "name": "repo"},
            "installation": {"id": 123},
        }
        
        # Execute
        with patch("services.webhook.screenshot_handler.GITHUB_APP_USER_NAME", "gitauto-for-dev[bot]"):
            result = await handle_screenshot_comparison(payload)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_no_target_paths(self, mock_dependencies):
        """Test that function returns early when no target paths are found."""
        # Setup
        payload = {
            "pull_request": {
                "user": {"login": "gitauto-for-dev[bot]"},
                "number": 123,
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "head": {"ref": "feature-branch"},
            },
            "repository": {"owner": {"login": "owner"}, "name": "repo"},
            "installation": {"id": 123},
        }
        
        mock_dependencies["get_target_paths"].return_value = []
        
        # Execute
        with patch("services.webhook.screenshot_handler.GITHUB_APP_USER_NAME", "gitauto-for-dev[bot]"):
            result = await handle_screenshot_comparison(payload)

        # Assert
        assert result is None
        mock_dependencies["get_target_paths"].assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_with_server_process_cleanup(self, mock_dependencies):
        """Test that server process is properly cleaned up."""
        # Setup
        payload = {
            "pull_request": {
                "user": {"login": "gitauto-for-dev[bot]"},
                "number": 123,
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "head": {"ref": "feature-branch"},
            },
            "repository": {"owner": {"login": "owner"}, "name": "repo"},
            "installation": {"id": 123},
        }
        
        # Mock server process
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_dependencies["start_local_server"].return_value = mock_server_process
        mock_dependencies["get_target_paths"].return_value = ["/"]
        
        # Mock os.path.exists and os.makedirs
        mock_dependencies["os"].path.exists.return_value = True
        mock_dependencies["os"].makedirs = MagicMock()
        
        # Execute
        with patch("services.webhook.screenshot_handler.GITHUB_APP_USER_NAME", "gitauto-for-dev[bot]"):
            result = await handle_screenshot_comparison(payload)

        # Assert
        assert result is None
        mock_server_process.terminate.assert_called_once()
        mock_server_process.wait.assert_called_once()
        mock_dependencies["shutil"].rmtree.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_screenshot_comparison_exception_handling(self, mock_dependencies):
        """Test that exceptions are handled and cleanup still occurs."""
        # Setup
        payload = {
            "pull_request": {
                "user": {"login": "gitauto-for-dev[bot]"},
                "number": 123,
                "url": "https://api.github.com/repos/owner/repo/pulls/123",
                "head": {"ref": "feature-branch"},
            },
            "repository": {"owner": {"login": "owner"}, "name": "repo"},
            "installation": {"id": 123},
        }
        
        # Mock server process
        mock_server_process = MagicMock()
        mock_server_process.pid = 12345
        mock_dependencies["start_local_server"].return_value = mock_server_process
        mock_dependencies["get_target_paths"].return_value = ["/"]
        
        # Make clone_repo raise an exception
        mock_dependencies["clone_repo"].side_effect = Exception("Clone failed")
        
        # Mock os.path.exists and os.makedirs
        mock_dependencies["os"].path.exists.return_value = True
        mock_dependencies["os"].makedirs = MagicMock()
        
        # Execute
        with patch("services.webhook.screenshot_handler.GITHUB_APP_USER_NAME", "gitauto-for-dev[bot]"):
            # Should not raise exception due to handle_exceptions decorator
            result = await handle_screenshot_comparison(payload)

        # Assert - cleanup should still occur even with exception
        assert result is None
        mock_server_process.terminate.assert_called_once()
        mock_server_process.wait.assert_called_once()
        mock_dependencies["shutil"].rmtree.assert_called_once()

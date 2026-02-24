# Standard imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Local imports
from utils.memory.is_lambda_oom_approaching import (
    LAMBDA_MEMORY_MB,
    is_lambda_oom_approaching,
)

# 90% of 2048 = 1843.2 MB
THRESHOLD_MB = LAMBDA_MEMORY_MB * 90 / 100


def _mock_rusage(ru_maxrss: int):
    rusage = MagicMock()
    rusage.ru_maxrss = ru_maxrss
    return rusage


class TestIsLambdaOomApproaching:

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_below_threshold_linux(self, mock_resource):
        # 1000 MB in KB (Linux units)
        mock_resource.getrusage.return_value = _mock_rusage(1000 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is False
        assert used_mb == 1000.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_above_threshold_linux(self, mock_resource):
        # 1900 MB in KB (above 1843.2 MB threshold)
        mock_resource.getrusage.return_value = _mock_rusage(1900 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 1900.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", True)
    @patch("utils.memory.get_rss_mb.resource")
    def test_below_threshold_macos(self, mock_resource):
        # 1000 MB in bytes (macOS units)
        mock_resource.getrusage.return_value = _mock_rusage(1000 * 1024 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is False
        assert used_mb == 1000.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", True)
    @patch("utils.memory.get_rss_mb.resource")
    def test_above_threshold_macos(self, mock_resource):
        # 1900 MB in bytes (macOS units)
        mock_resource.getrusage.return_value = _mock_rusage(1900 * 1024 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 1900.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_exact_threshold_not_approaching(self, mock_resource):
        # Exactly at threshold (1843.2 MB) - use 1843 MB, not greater, so False
        mock_resource.getrusage.return_value = _mock_rusage(1843 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is False
        assert used_mb == 1843.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_just_above_threshold(self, mock_resource):
        # 1844 MB - just above 1843.2 threshold
        mock_resource.getrusage.return_value = _mock_rusage(1844 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 1844.0

    @pytest.mark.parametrize(
        "used_kb, expected_approaching",
        [
            (0, False),
            (512 * 1024, False),
            (1024 * 1024, False),
            (1843 * 1024, False),
            (1844 * 1024, True),
            (2048 * 1024, True),
        ],
        ids=["zero", "512mb", "1024mb", "at_threshold", "above_threshold", "at_limit"],
    )
    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_parametrized_linux(self, mock_resource, used_kb, expected_approaching):
        mock_resource.getrusage.return_value = _mock_rusage(used_kb)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, _ = is_lambda_oom_approaching()
        assert is_approaching is expected_approaching

    def test_has_handle_exceptions_decorator(self):
        assert hasattr(is_lambda_oom_approaching, "__wrapped__")

    def test_constant_matches_infrastructure(self):
        assert LAMBDA_MEMORY_MB == 2048

# Standard imports
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Local imports
from utils.memory.is_lambda_oom_approaching import (
    LAMBDA_MEMORY_MB,
    is_lambda_oom_approaching,
)

# 90% of 3072 = 2764.8 MB
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
        # 2800 MB in KB (above 2764.8 MB threshold)
        mock_resource.getrusage.return_value = _mock_rusage(2800 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 2800.0

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
        # 2800 MB in bytes (macOS units)
        mock_resource.getrusage.return_value = _mock_rusage(2800 * 1024 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 2800.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_exact_threshold_not_approaching(self, mock_resource):
        # Exactly at threshold (2764.8 MB) - use 2764 MB, not greater, so False
        mock_resource.getrusage.return_value = _mock_rusage(2764 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is False
        assert used_mb == 2764.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_just_above_threshold(self, mock_resource):
        # 2765 MB - just above 2764.8 threshold
        mock_resource.getrusage.return_value = _mock_rusage(2765 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 2765.0

    @pytest.mark.parametrize(
        "used_kb, expected_approaching",
        [
            (0, False),
            (512 * 1024, False),
            (1024 * 1024, False),
            (2764 * 1024, False),
            (2765 * 1024, True),
            (3072 * 1024, True),
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
        assert LAMBDA_MEMORY_MB == 3072

# Standard imports
import importlib
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest

# Local imports
import utils.memory.is_lambda_oom_approaching as oom_module
from utils.memory.is_lambda_oom_approaching import (
    LAMBDA_MEMORY_MB,
    NODE_MAX_OLD_SPACE_SIZE_MB,
    is_lambda_oom_approaching,
)

# 90% of 4096 = 3686.4 MB
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
        # 3700 MB in KB (above 3686.4 MB threshold)
        mock_resource.getrusage.return_value = _mock_rusage(3700 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 3700.0

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
        # 3700 MB in bytes (macOS units)
        mock_resource.getrusage.return_value = _mock_rusage(3700 * 1024 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 3700.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_exact_threshold_not_approaching(self, mock_resource):
        # Exactly at threshold (3686.4 MB) - use 3686 MB, not greater, so False
        mock_resource.getrusage.return_value = _mock_rusage(3686 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is False
        assert used_mb == 3686.0

    @patch("utils.memory.get_rss_mb._IS_MACOS", False)
    @patch("utils.memory.get_rss_mb.resource")
    def test_just_above_threshold(self, mock_resource):
        # 3687 MB - just above 3686.4 threshold
        mock_resource.getrusage.return_value = _mock_rusage(3687 * 1024)
        mock_resource.RUSAGE_SELF = 0
        is_approaching, used_mb = is_lambda_oom_approaching()
        assert is_approaching is True
        assert used_mb == 3687.0

    @pytest.mark.parametrize(
        "used_kb, expected_approaching",
        [
            (0, False),
            (512 * 1024, False),
            (1024 * 1024, False),
            (3686 * 1024, False),
            (3687 * 1024, True),
            (4096 * 1024, True),
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

    def test_default_matches_infrastructure(self):
        assert LAMBDA_MEMORY_MB == 4096

    @patch.dict("os.environ", {"AWS_LAMBDA_FUNCTION_MEMORY_SIZE": "4096"})
    def test_reads_memory_from_env_var(self):
        importlib.reload(oom_module)
        assert oom_module.LAMBDA_MEMORY_MB == 4096
        assert oom_module.NODE_MAX_OLD_SPACE_SIZE_MB == 4096 - 1536
        # Restore default for other tests
        importlib.reload(oom_module)

    def test_node_max_old_space_size_derivation(self):
        assert NODE_MAX_OLD_SPACE_SIZE_MB == LAMBDA_MEMORY_MB - 1536

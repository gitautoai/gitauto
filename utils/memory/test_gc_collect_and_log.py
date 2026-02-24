from unittest.mock import patch

from utils.memory.gc_collect_and_log import gc_collect_and_log


def test_gc_collect_and_log_runs_without_error():
    gc_collect_and_log()


@patch("utils.memory.gc_collect_and_log.gc.collect", return_value=42)
def test_gc_collect_and_log_calls_gc(mock_gc):
    gc_collect_and_log()
    mock_gc.assert_called_once()

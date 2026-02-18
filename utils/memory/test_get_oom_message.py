# Local imports
from utils.memory.get_oom_message import get_oom_message
from utils.memory.is_lambda_oom_approaching import LAMBDA_MEMORY_MB


def test_default_process_name():
    msg = get_oom_message(1800.0)
    assert (
        msg
        == f"Process stopped due to memory limit (1800MB / {LAMBDA_MEMORY_MB}MB used). Proceeding with current progress."
    )


def test_custom_process_name():
    msg = get_oom_message(1900.0, "issue processing")
    assert "issue processing stopped" in msg
    assert "1900MB" in msg


def test_rounds_to_integer():
    msg = get_oom_message(1799.7)
    assert "1800MB" in msg


def test_has_handle_exceptions_decorator():
    assert hasattr(get_oom_message, "__wrapped__")

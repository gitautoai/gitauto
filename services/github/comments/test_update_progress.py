# pyright: reportUnusedVariable=false
import inspect
from unittest.mock import MagicMock, patch

from services.github.comments.update_progress import update_progress


@patch("services.github.comments.update_progress.update_comment")
@patch("services.github.comments.update_progress.create_progress_bar")
@patch("services.github.comments.update_progress.add_log_message")
def test_update_progress_returns_incremented_p(
    mock_add_log, mock_progress_bar, mock_update_comment
):
    mock_progress_bar.return_value = "progress bar"
    base_args = MagicMock()
    log_messages: list[str] = []

    result = update_progress(
        msg="Test", p=10, log_messages=log_messages, base_args=base_args
    )

    assert result == 15
    mock_add_log.assert_called_once_with("Test", log_messages)
    mock_progress_bar.assert_called_once()
    mock_update_comment.assert_called_once()


@patch("services.github.comments.update_progress.update_comment")
@patch("services.github.comments.update_progress.create_progress_bar")
@patch("services.github.comments.update_progress.add_log_message")
def test_update_progress_exception_returns_default(
    _mock_add_log, _mock_progress_bar, mock_update_comment
):
    mock_update_comment.side_effect = Exception("API error")
    base_args = MagicMock()

    result = update_progress(msg="Test", p=10, log_messages=[], base_args=base_args)

    assert result == 0


def test_update_progress_function_signature():
    sig = inspect.signature(update_progress)
    params = list(sig.parameters.keys())
    assert params == ["msg", "p", "log_messages", "base_args"]


def test_update_progress_decorator_applied():
    assert hasattr(update_progress, "__wrapped__")

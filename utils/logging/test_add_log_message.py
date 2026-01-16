from unittest.mock import patch

from utils.logging.add_log_message import add_log_message


@patch("utils.logging.add_log_message.logger")
def test_add_log_message_logs_and_appends(mock_logger):
    log_messages = []
    msg = "Test message"

    add_log_message(msg, log_messages)

    mock_logger.info.assert_called_once_with(msg)
    assert log_messages == ["Test message"]


@patch("utils.logging.add_log_message.logger")
def test_add_log_message_appends_to_existing_list(mock_logger):
    log_messages = ["Existing message"]
    msg = "New message"

    add_log_message(msg, log_messages)

    mock_logger.info.assert_called_once_with(msg)
    assert log_messages == ["Existing message", "New message"]


@patch("utils.logging.add_log_message.logger")
def test_add_log_message_multiple_calls(mock_logger):
    log_messages = []

    add_log_message("First", log_messages)
    add_log_message("Second", log_messages)
    add_log_message("Third", log_messages)

    assert mock_logger.info.call_count == 3
    assert log_messages == ["First", "Second", "Third"]

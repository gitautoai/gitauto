from unittest.mock import MagicMock, patch

from utils.logging.logging_config import clear_state


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_clear_state_calls_logger_clear_state_in_prd(mock_logger):
    mock_logger.clear_state = MagicMock()
    clear_state()
    mock_logger.clear_state.assert_called_once()


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_clear_state_does_nothing_in_non_prd(mock_logger):
    mock_logger.clear_state = MagicMock()
    clear_state()
    mock_logger.clear_state.assert_not_called()

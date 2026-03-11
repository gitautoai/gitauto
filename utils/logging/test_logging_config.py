import importlib
import sys
from unittest.mock import MagicMock, patch

from utils.logging.logging_config import (clear_state, set_event_action,
                                          set_owner_repo, set_pr_number,
                                          set_request_id, set_trigger)


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


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_request_id_calls_append_keys_in_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_request_id("abc-123")
    mock_logger.append_keys.assert_called_once_with(request_id="abc-123")


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_set_request_id_does_nothing_in_non_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_request_id("abc-123")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_owner_repo_calls_append_keys_in_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_owner_repo("gitautoai", "gitauto")
    mock_logger.append_keys.assert_called_once_with(owner_repo="gitautoai/gitauto")


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_set_owner_repo_does_nothing_in_non_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_owner_repo("gitautoai", "gitauto")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_owner_repo_does_nothing_when_owner_empty(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_owner_repo("", "gitauto")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_owner_repo_does_nothing_when_repo_empty(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_owner_repo("gitautoai", "")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_pr_number_calls_append_keys_in_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_pr_number(42)
    mock_logger.append_keys.assert_called_once_with(pr_number=42)


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_set_pr_number_does_nothing_in_non_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_pr_number(42)
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_pr_number_does_nothing_when_zero(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_pr_number(0)
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_event_action_calls_append_keys_in_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_event_action("pull_request", "opened")
    mock_logger.append_keys.assert_called_once_with(
        event_action="pull_request_opened"
    )


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_set_event_action_does_nothing_in_non_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_event_action("pull_request", "opened")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_event_action_does_nothing_when_event_name_empty(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_event_action("", "opened")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_event_action_does_nothing_when_action_empty(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_event_action("pull_request", "")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_trigger_calls_append_keys_in_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_trigger("dashboard")
    mock_logger.append_keys.assert_called_once_with(trigger="dashboard")


@patch("utils.logging.logging_config.IS_PRD", False)
@patch("utils.logging.logging_config.logger")
def test_set_trigger_does_nothing_in_non_prd(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_trigger("dashboard")
    mock_logger.append_keys.assert_not_called()


@patch("utils.logging.logging_config.IS_PRD", True)
@patch("utils.logging.logging_config.logger")
def test_set_trigger_does_nothing_when_trigger_empty(mock_logger):
    mock_logger.append_keys = MagicMock()
    set_trigger("")
    mock_logger.append_keys.assert_not_called()

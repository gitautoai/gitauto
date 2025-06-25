import asyncio
import json

import pytest

from services.webhook import check_run_handler, issue_handler, push_handler, review_run_handler

# Dummy system messages to be returned by create_system_messages
DUMMY_SYSTEM_MESSAGES = [{"role": "system", "content": "dummy system message"}]


# Dummy chat_with_agent to capture the system_messages parameter
class ChatWithAgentRecorder:
    def __init__(self):
        self.captured = None

    def dummy_chat_with_agent(self, *args, **kwargs):
        self.captured = kwargs.get("system_messages")
        # Return a dummy tuple with the expected number of return values
        # The actual return values are not used in these tests
        return (None, 0, 0, None)


# Test for handle_check_run in check_run_handler

def test_handle_check_run(monkeypatch):
    recorder = ChatWithAgentRecorder()
    # Patch create_system_messages to return DUMMY_SYSTEM_MESSAGES
    monkeypatch.setattr(check_run_handler, "create_system_messages", lambda repo_settings: DUMMY_SYSTEM_MESSAGES)
    # Patch chat_with_agent in the check_run_handler module
    monkeypatch.setattr(check_run_handler, "chat_with_agent", recorder.dummy_chat_with_agent)

    payload = {"user_input": "test input", "repo_settings": {"dummy": True}}
    # Call the handler
    check_run_handler.handle_check_run(payload)
    
    # Assert that chat_with_agent was called with the DUMMY_SYSTEM_MESSAGES
    assert recorder.captured == DUMMY_SYSTEM_MESSAGES


# Test for create_pr_from_issue in issue_handler (async function)
@pytest.mark.asyncio
async def test_create_pr_from_issue(monkeypatch):
    recorder = ChatWithAgentRecorder()
    # Patch create_system_messages to return DUMMY_SYSTEM_MESSAGES
    monkeypatch.setattr(issue_handler, "create_system_messages", lambda repo_settings: DUMMY_SYSTEM_MESSAGES)
    # Patch chat_with_agent in issue_handler module
    monkeypatch.setattr(issue_handler, "chat_with_agent", recorder.dummy_chat_with_agent)

    # Prepare a dummy payload with required keys
    payload = {"user_input": "issue test input", "repo_settings": {"dummy": True}}
    # Call the async handler
    await issue_handler.create_pr_from_issue(payload)
    
    # Assert that chat_with_agent was called with the DUMMY_SYSTEM_MESSAGES
    assert recorder.captured == DUMMY_SYSTEM_MESSAGES


# Test for handle_push_event in push_handler

def test_handle_push_event(monkeypatch):
    recorder = ChatWithAgentRecorder()
    # Patch create_system_messages in push_handler to return DUMMY_SYSTEM_MESSAGES
    monkeypatch.setattr(push_handler, "create_system_messages", lambda repo_settings: DUMMY_SYSTEM_MESSAGES)
    # Patch chat_with_agent in push_handler module
    monkeypatch.setattr(push_handler, "chat_with_agent", recorder.dummy_chat_with_agent)

    # PUSH_TRIGGER_SYSTEM_PROMPT is used in constructing system_messages
    from services.webhook.push_handler import PUSH_TRIGGER_SYSTEM_PROMPT
    # Expected system messages: system prompt plus the dummy messages
    expected_system_messages = [{"role": "system", "content": PUSH_TRIGGER_SYSTEM_PROMPT}] + DUMMY_SYSTEM_MESSAGES

    payload = {"repo_settings": {"dummy": True}, "input_message": {"key": "value"}}
    push_handler.handle_push_event(payload)
    
    # Assert that chat_with_agent was called with the expected system_messages
    assert recorder.captured == expected_system_messages


# Test for handle_review_run in review_run_handler

def test_handle_review_run(monkeypatch):
    recorder = ChatWithAgentRecorder()
    # Patch create_system_messages in review_run_handler to return DUMMY_SYSTEM_MESSAGES
    monkeypatch.setattr(review_run_handler, "create_system_messages", lambda repo_settings: DUMMY_SYSTEM_MESSAGES)
    # Patch chat_with_agent in review_run_handler module
    monkeypatch.setattr(review_run_handler, "chat_with_agent", recorder.dummy_chat_with_agent)

    payload = {"user_input": "review test input", "repo_settings": {"dummy": True}}
    review_run_handler.handle_review_run(payload)

    # Assert that chat_with_agent was called with the DUMMY_SYSTEM_MESSAGES
    assert recorder.captured == DUMMY_SYSTEM_MESSAGES

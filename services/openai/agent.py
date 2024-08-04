# Standard imports
import json
import logging
import time
from typing import Any
import difflib

# Third-party imports
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, Message, TextContentBlock
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput

# Local imports
from config import (
    OPENAI_FINAL_STATUSES,
    OPENAI_MAX_STRING_LENGTH,
    OPENAI_MODEL_ID,
    TIMEOUT_IN_SECONDS,
)
from services.openai.functions import (
    GET_REMOTE_FILE_CONTENT,
    functions,
    REASON_FOR_MODYING_DIFF,
)
from services.openai.init import create_openai_client
from services.openai.instructions import (
    SYSTEM_INSTRUCTION_FOR_AGENT,
    SYSTEM_INSTRUCTION_FOR_AGENT_REVIEW_DIFFS,
)
from services.github.github_manager import (
    commit_multiple_changes_to_remote_branch,
    update_comment,
)
from utils.file_manager import (
    clean_specific_lines,
    correct_hunk_headers,
    split_diffs,
)
from utils.handle_exceptions import handle_exceptions
from utils.progress_bar import generate_progress_bar


def create_assistant() -> tuple[Assistant, str]:
    """Create Open AI client and then create the assistant."""
    client: OpenAI = create_openai_client()
    input_data = json.dumps(
        {
            "name": "GitAuto: Automated Issue Resolver",
            "instructions": SYSTEM_INSTRUCTION_FOR_AGENT,
            "tools": [
                # {"type": "code_interpreter"},
                # {"type": "retrieval"},
                {"type": "function", "function": GET_REMOTE_FILE_CONTENT}
            ],
        }
    )
    return (
        client.beta.assistants.create(
            name="GitAuto: Automated Issue Resolver",
            instructions=SYSTEM_INSTRUCTION_FOR_AGENT,
            tools=[
                # {"type": "code_interpreter"},
                # {"type": "retrieval"},
                {"type": "function", "function": GET_REMOTE_FILE_CONTENT},
                {"type": "function", "function": REASON_FOR_MODYING_DIFF},
            ],
            model=OPENAI_MODEL_ID,
            timeout=TIMEOUT_IN_SECONDS,
        ),
        input_data,
    )


def create_thread_and_run(
    user_input: str,
) -> tuple[OpenAI, Assistant, Thread, Run, str]:
    """thread represents a conversation. 1 thread per 1 issue.
    Assistants API will manage the context window.
    https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    thread: Thread = client.beta.threads.create(timeout=TIMEOUT_IN_SECONDS)
    assistant, input_data = create_assistant()
    run, submit_message_input_data = submit_message(
        client=client, assistant=assistant, thread=thread, user_message=user_input
    )
    input_data += submit_message_input_data
    return client, assistant, thread, run, input_data


def get_response(thread: Thread) -> SyncCursorPage[Message]:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    return client.beta.threads.messages.list(
        thread_id=thread.id, order="desc", timeout=TIMEOUT_IN_SECONDS
    )


def run_assistant(
    file_paths: list[str],
    issue_title: str,
    issue_body: str,
    issue_comments: list[str],
    owner: str,
    pr_body: str,
    ref: str,
    repo: str,
    comment_url: str,
    token: str,
    new_branch: str,
) -> tuple[int, int]:
    # Create a message in the thread
    data: dict[str, str | list[str]] = {
        "owner": owner,
        "pr_body": pr_body,
        "repo": repo,
        "ref": ref,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issue_comments": issue_comments,
        "file_paths": file_paths,
        "comment_url": comment_url,
        "new_branch": new_branch,
    }
    user_input: str = json.dumps(obj=data)

    # Run the assistant
    client, assistant, thread, run, input_data = create_thread_and_run(
        user_input=user_input
    )

    # Wait for the run to complete, handle function calling if necessary
    run, input_output_data = wait_on_run(
        run=run, thread=thread, token=token, run_name="generate diffs"
    )
    input_data += input_output_data
    output_data: str = input_output_data

    # Get the response
    messages: SyncCursorPage[Message] = get_response(thread=thread)
    messages_list = list(messages)
    if not messages_list:
        msg = f"In run_assistant(), messages_list is empty: '{messages_list}'"
        raise ValueError(msg)
    latest_message: Message = messages_list[0]
    if not latest_message.content:
        msg = f"In run_assistant(), latest_message.content is empty. latest_message: '{latest_message}'"
        raise ValueError(msg)
    if isinstance(latest_message.content[0], TextContentBlock):
        value: str = latest_message.content[0].text.value
        output_data += json.dumps(latest_message.content[0].text.value)
    else:
        msg = f"In run_assistant(), Last message content is not text. latest_message: '{latest_message}'"
        raise ValueError(msg)

    # Clean the diff text and split it
    diff: str = clean_specific_lines(text=value)
    text_diffs: list[str] = split_diffs(diff_text=diff)
    first_run_output: list[str] = []
    for diff in text_diffs:
        diff = correct_hunk_headers(diff_text=diff)
        first_run_output.append(diff)

    update_comment(
        comment_url=comment_url,
        token=token,
        body=generate_progress_bar(p=50),
    )

    # Self review diff
    self_review_run, self_review_input_data = submit_message(
        client,
        assistant,
        thread,
        SYSTEM_INSTRUCTION_FOR_AGENT_REVIEW_DIFFS + json.dumps(first_run_output),
    )
    input_data += self_review_input_data

    self_review_run, self_review_input_data = wait_on_run(
        run=self_review_run, thread=thread, token=token, run_name="review diffs"
    )
    input_data += self_review_input_data

    # Get the response
    messages: SyncCursorPage[Message] = get_response(thread=thread)
    messages_list = list(messages)
    if not messages_list:
        raise ValueError("No messages in the list.")
    latest_message: Message = messages_list[0]
    if isinstance(latest_message.content[0], TextContentBlock):
        value: str = latest_message.content[0].text.value
        output_data += json.dumps(latest_message.content[0].text.value)
    else:
        raise ValueError("Last message content is not text.")

    # Clean the diff text and split it
    diff: str = clean_specific_lines(text=value)
    text_diffs: list[str] = split_diffs(diff_text=diff)
    output: list[str] = []
    i = 0
    for diff in text_diffs:
        diff = correct_hunk_headers(diff_text=diff)
        # Show difference between the create diff and the modified diff
        if i < len(first_run_output):
            difference_from_first = "\n".join(
                difflib.unified_diff(
                    first_run_output[i].splitlines(), diff.splitlines(), lineterm=""
                )
            )
            print(f"Difference from first: {difference_from_first}\n")
        output.append(diff)
        i += 1

    commit_multiple_changes_to_remote_branch(
        diffs=output,
        new_branch=new_branch,
        owner=owner,
        repo=repo,
        token=token,
    )

    update_comment(
        comment_url=comment_url,
        token=token,
        body=generate_progress_bar(p=80),
    )

    output_data += json.dumps(output)

    # One token is ~4 characters of text https://platform.openai.com/tokenizer
    token_input = int(len(input_data) / 4)
    token_output = int(len(output_data) / 4)

    return token_input, token_output


@handle_exceptions(raise_on_error=True)
def submit_message(
    client: OpenAI, assistant: Assistant, thread: Thread, user_message: str
) -> tuple[Run, str]:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    # Ensure the message string length is <= 256,000 characters. See https://community.openai.com/t/assistant-threads-create-400-messages-array-too-long/754574/5
    for i in range(0, len(user_message), OPENAI_MAX_STRING_LENGTH):
        chunk = user_message[i : i + OPENAI_MAX_STRING_LENGTH]  # noqa: E203
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=chunk,
            timeout=TIMEOUT_IN_SECONDS,
        )
    input_data = json.dumps({"role": "'user", "content": str(user_message)})
    return (
        client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, timeout=TIMEOUT_IN_SECONDS
        ),
        input_data,
    )


def wait_on_run(run: Run, thread: Thread, token: str, run_name: str) -> tuple[Run, str]:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    input_data = ""
    while run.status not in OPENAI_FINAL_STATUSES:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id, timeout=TIMEOUT_IN_SECONDS
        )

        # If the run requires action, call the function and run again with the output
        if run.status == "requires_action":
            try:
                tool_outputs: list[Any] = call_functions(
                    run=run, funcs=functions, token=token
                )

                # The combined tool outputs must be less than 512kb.
                tool_outputs_json: list[ToolOutput] = [
                    {"tool_call_id": tool_call.id, "output": json.dumps(obj=result)}
                    for tool_call, result in tool_outputs
                ]
                input_data += json.dumps(tool_outputs_json)
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs_json,
                    timeout=TIMEOUT_IN_SECONDS,
                )
            except Exception as e:
                raise ValueError(f"Error: {e}") from e
        time.sleep(0.5)

    # Loop is done, check if the run failed
    # See https://platform.openai.com/docs/api-reference/runs/object#runs/object-last_error
    if run.status == "failed":
        logging.error("Run %s failed: %s", run_name, run.last_error)
    return run, input_data


def call_functions(run: Run, funcs: dict[str, Any], token: str) -> list[Any]:
    # Raise an error if there is no tool call in the run
    if run.required_action is None:
        raise ValueError("No tool call in the run.")

    # Get the tool calls
    results: list[Any] = []
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        name: str = tool_call.function.name
        args = json.loads(s=tool_call.function.arguments)
        args["token"] = token
        print(f"{name=}\n{args=}\n")

        if name not in funcs:
            print(f"Function not found: {name}, skipping it.")
            continue

        # Call the function if it exists
        try:
            func: Any = funcs[name]
            result: Any = func(**args)
            results.append((tool_call, result))
        except KeyError as e:
            raise ValueError(f"call_functions Function not found: {e}") from e
        except Exception as e:
            raise ValueError(f"call_functions Error: {e}") from e

    return results

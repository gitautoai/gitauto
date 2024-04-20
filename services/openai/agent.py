# Standard imports
from email import message
import json
import time
from typing import Any

# Third-party imports
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, ThreadMessage, MessageContentText
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput
import tiktoken

# Local imports
from config import OPENAI_FINAL_STATUSES, OPENAI_MODEL_ID, TIMEOUT_IN_SECONDS
from services.openai.functions import GET_REMOTE_FILE_CONTENT, functions
from services.openai.init import create_openai_client
from services.openai.instructions import SYSTEM_INSTRUCTION_FOR_AGENT
from utils.file_manager import clean_specific_lines, correct_hunk_headers, split_diffs


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
            "model": OPENAI_MODEL_ID,
            "timeout": TIMEOUT_IN_SECONDS,
        }
    )
    return (
        client.beta.assistants.create(
            name="GitAuto: Automated Issue Resolver",
            instructions=SYSTEM_INSTRUCTION_FOR_AGENT,
            tools=[
                # {"type": "code_interpreter"},
                # {"type": "retrieval"},
                {"type": "function", "function": GET_REMOTE_FILE_CONTENT}
            ],
            model=OPENAI_MODEL_ID,
            timeout=TIMEOUT_IN_SECONDS,
        ),
        input_data,
    )


def create_thread_and_run(user_input: str) -> tuple[Thread, Run, str]:
    """thread represents a conversation. 1 thread per 1 issue.
    Assistants API will manage the context window.
    https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    thread: Thread = client.beta.threads.create(timeout=TIMEOUT_IN_SECONDS)
    run, input_data = submit_message(thread=thread, user_message=user_input)
    return thread, run, input_data


def get_response(thread: Thread) -> SyncCursorPage[ThreadMessage]:
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
    token: str,
) -> tuple[int, int, list[str]]:
    """Starts the Assistants API and the flow of GitAuto Agent."""

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
    }
    issue_input: str = json.dumps(obj=data)

    # Run the assistant
    thread, run, input_data = create_thread_and_run(user_input=issue_input)
    print(f"Thread is created: {thread.id}\n")
    print(f"Run is created: {run.id}\n")

    # Wait for the run to complete, handle function calling if necessary
    run, input_output_data = wait_on_run(run=run, thread=thread, token=token)
    input_data += input_output_data
    output_data = input_output_data

    # Get the response
    messages: SyncCursorPage[ThreadMessage] = get_response(thread=thread)
    messages_list = list(messages)
    if not messages_list:
        raise ValueError("No messages in the list.")
    latest_message: ThreadMessage = messages_list[0]
    if isinstance(latest_message.content[0], MessageContentText):
        value: str = latest_message.content[0].text.value
        output_data += json.dumps(latest_message.content[0].text.value)
    else:
        raise ValueError("Last message content is not text.")
    print(f"Last message: {value}\n")

    # Clean the diff text and split it
    diff: str = clean_specific_lines(text=value)
    text_diffs: list[str] = split_diffs(diff_text=diff)
    output: list[str] = []
    for diff in text_diffs:
        diff = correct_hunk_headers(diff_text=diff)
        print(f"Diff: {repr(diff)}\n")
        output.append(diff)

    try:
        encoding = tiktoken.encoding_for_model(OPENAI_MODEL_ID)
    except Exception as e:
        print(e)
    output_data += json.dumps(output)
    token_input = len(encoding.encode(input_data))
    token_output = len(encoding.encode(json.dumps(output)))

    return token_input, token_output, output


def submit_message(thread: Thread, user_message: str) -> tuple[Run, str]:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    assistant, input_data = create_assistant()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message,
        timeout=TIMEOUT_IN_SECONDS,
    )
    input_data += json.dumps(
        {
            "thread_id": str(thread.id),
            "content": str(user_message),
            "role": "'user",
            "timeout": str(TIMEOUT_IN_SECONDS),
        }
    )
    return (
        client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, timeout=TIMEOUT_IN_SECONDS
        ),
        input_data,
    )


def wait_on_run(run: Run, thread: Thread, token: str) -> tuple[Run, str]:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    print(f"Run status before loop: {run.status}")
    client: OpenAI = create_openai_client()
    input_output_data = ""
    while run.status not in OPENAI_FINAL_STATUSES:
        print(f"Run status during loop: {run.status}")
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id, timeout=TIMEOUT_IN_SECONDS
        )

        # If the run requires action, call the function and run again with the output
        if run.status == "requires_action":
            print("Run requires action")
            try:
                tool_outputs: list[Any] = call_functions(
                    run=run, funcs=functions, token=token
                )

                tool_outputs_json: list[ToolOutput] = [
                    {"tool_call_id": tool_call.id, "output": json.dumps(obj=result)}
                    for tool_call, result in tool_outputs
                ]
                input_output_data += json.dumps(tool_outputs_json)
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs_json,
                    timeout=TIMEOUT_IN_SECONDS,
                )
            except Exception as e:
                raise ValueError(f"Error: {e}") from e
        time.sleep(0.5)
    print(f"Run status after loop: {run.status}")
    return run, input_output_data


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
            raise ValueError(f"Function not found: {e}") from e
        except Exception as e:
            raise ValueError(f"Error: {e}") from e

    return results

# Standard imports
import json
import logging
import time
from typing import Any, Iterable

# Third-party imports
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.assistant_tool_param import AssistantToolParam
from openai.types.beta.threads import Run, Message
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput

# Local imports
from config import (
    OPENAI_ASSISTANT_NAME,
    OPENAI_FINAL_STATUSES,
    OPENAI_MAX_STRING_LENGTH,
    OPENAI_MAX_TOOL_OUTPUTS_SIZE,
    OPENAI_MODEL_ID,
    OPENAI_TEMPERATURE,
    TIMEOUT,
    UTF8,
)
from services.github.github_manager import update_comment
from services.github.github_types import BaseArgs
from services.openai.functions import (
    COMMIT_CHANGES_TO_REMOTE_BRANCH,
    GET_REMOTE_FILE_CONTENT,
    SEARCH_REMOTE_FILE_CONTENT,
    functions,
)
from services.openai.init import create_openai_client
from services.openai.instructions.index import SYSTEM_INSTRUCTION_FOR_AGENT
from utils.handle_exceptions import handle_exceptions
from utils.progress_bar import create_progress_bar


def create_assistant() -> tuple[Assistant, str]:
    """
    Create Open AI client and then create the assistant.
    https://platform.openai.com/docs/api-reference/assistants/createAssistant
    """
    client: OpenAI = create_openai_client()
    tools: Iterable[AssistantToolParam] = [
        # {"type": "code_interpreter"},
        # {"type": "retrieval"},
        {"type": "function", "function": COMMIT_CHANGES_TO_REMOTE_BRANCH},
        {"type": "function", "function": GET_REMOTE_FILE_CONTENT},
        {"type": "function", "function": SEARCH_REMOTE_FILE_CONTENT},
    ]
    input_data = json.dumps(
        {
            "name": OPENAI_ASSISTANT_NAME,
            "instructions": SYSTEM_INSTRUCTION_FOR_AGENT,
            "tools": tools,
        }
    )
    return (
        client.beta.assistants.create(
            name=OPENAI_ASSISTANT_NAME,
            instructions=SYSTEM_INSTRUCTION_FOR_AGENT,
            tools=tools,
            model=OPENAI_MODEL_ID,
            temperature=OPENAI_TEMPERATURE,
            timeout=TIMEOUT,
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
    thread: Thread = client.beta.threads.create(timeout=TIMEOUT)
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
        thread_id=thread.id, order="desc", timeout=TIMEOUT
    )


@handle_exceptions(raise_on_error=True)
def run_assistant(
    issue_title: str,
    issue_body: str,
    reference_contents: list[str],
    issue_comments: list[str],
    root_files_and_dirs: list[str],
    base_args: BaseArgs,
) -> tuple[int, int]:
    # Create a message in the thread
    owner, repo, comment_url, pr_body, token = (
        base_args["owner"],
        base_args["repo"],
        base_args["comment_url"],
        base_args["pr_body"],
        base_args["token"],
    )
    data: dict[str, str | list[str]] = {
        "owner": owner,
        "repo": repo,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "reference_contents": reference_contents,
        "issue_comments": issue_comments,
        "pr_body": pr_body,
        "root_files_and_dirs": root_files_and_dirs,
    }
    user_input: str = json.dumps(obj=data)

    # Run the assistant
    _c, _a, thread, run, input_data = create_thread_and_run(user_input=user_input)

    # Wait for the run to complete, handle function calling if necessary
    comment_body = create_progress_bar(p=40, msg="Creating diffs...")
    update_comment(comment_url=comment_url, token=token, body=comment_body)
    run_name = "generate diffs"
    run, input_output_data = wait_on_run(
        run=run, thread=thread, run_name=run_name, base_args=base_args
    )

    # One token is ~4 characters of text https://platform.openai.com/tokenizer
    input_data += input_output_data
    output_data: str = input_output_data
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
            timeout=TIMEOUT,
        )
    input_data = json.dumps({"role": "'user", "content": str(user_message)})
    return (
        client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, timeout=TIMEOUT
        ),
        input_data,
    )


def wait_on_run(
    run: Run, thread: Thread, base_args: BaseArgs, run_name: str
) -> tuple[Run, str]:
    """
    https://cookbook.openai.com/examples/assistants_api_overview_python
    https://platform.openai.com/docs/api-reference/runs/cancelRun
    """
    client: OpenAI = create_openai_client()
    input_data = ""
    processed_calls = set()
    p = 40
    while run.status not in OPENAI_FINAL_STATUSES:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id, timeout=TIMEOUT
        )

        # If the run requires action, call the function and run again with the output
        if run.status != "requires_action":
            time.sleep(0.5)
            continue

        try:
            tool_outputs = call_functions(
                run=run, base_args=base_args, processed_calls=processed_calls, p=p
            )
            if not tool_outputs:
                client.beta.threads.runs.cancel(thread_id=thread.id, run_id=run.id)
                return run, input_data

            tool_outputs_json: list[ToolOutput] = [
                {"tool_call_id": tool_call.id, "output": json.dumps(obj=result)}
                for tool_call, result in tool_outputs
            ]

            # Update the progress rate
            p = p + 5 if p + 5 <= 90 else 90

            # The combined tool outputs must be less than 512kb.
            input_data += json.dumps(tool_outputs_json)
            input_data_size = len(input_data.encode(UTF8))
            if input_data_size < OPENAI_MAX_TOOL_OUTPUTS_SIZE:
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs_json,
                    timeout=TIMEOUT,
                )
        except Exception as e:  # pylint: disable=broad-except
            if "the combined tool outputs must be less than 512kb" in str(e):
                logging.warning("Tool outputs too large, skipping this submission.")
            else:
                raise ValueError(f"Error: {e}") from e

    # Loop is done, check if the run failed
    # See https://platform.openai.com/docs/api-reference/runs/object#runs/object-last_error
    if run.status == "failed":
        logging.error("Run %s failed: %s", run_name, run.last_error)
    return run, input_data


def call_functions(
    run: Run, base_args: BaseArgs, processed_calls: set, p: int
) -> list[Any]:
    # Raise an error if there is no tool call in the run
    if run.required_action is None:
        raise ValueError("No tool call in the run.")
    # Get the tool calls
    results: list[Any] = []
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        name: str = tool_call.function.name
        args: dict[str, Any] = json.loads(s=tool_call.function.arguments)

        # Update the comment
        comment_url = base_args["comment_url"]
        token = base_args["token"]
        args_copy = args.copy()
        if "diff" in args_copy:
            args_copy["diff"] = "..."
        msg = f"Running function: {name} with args: {args_copy}"
        body = create_progress_bar(p=p, msg=msg)
        update_comment(comment_url=comment_url, token=token, body=body)

        # Skip duplicate calls
        call_signature = (name, json.dumps(args, sort_keys=True))
        if call_signature in processed_calls:
            msg = f"Skipping duplicate call: '{name}' with '{args}'\n"
            logging.error(msg)
            return []
        processed_calls.add(call_signature)

        # Skip the function if it doesn't exist
        if name not in functions:
            print(f"Function not found: {name}, skipping it.")
            continue

        # Call the function if it exists
        try:
            func: Any = functions[name]
            args["base_args"] = base_args
            result: Any = func(**args)
            results.append((tool_call, result))
        except KeyError as e:
            raise ValueError(f"call_functions Function not found: {e}") from e
        except Exception as e:
            raise ValueError(f"call_functions Error: {e}") from e

    return results

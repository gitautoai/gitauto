# Standard imports
import json
import time
from typing import Any

# Third-party imports
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, ThreadMessage, MessageContentText
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput

# Local imports
from config import OPENAI_FINAL_STATUSES, OPENAI_MODEL_ID, TIMEOUT_IN_SECONDS
from services.openai.functions import (
    GET_REMOTE_FILE_CONTENT,
    functions,
    COMMIT_MULTIPLE_CHANGES_TO_REMOTE_BRANCH,
    WHY_MODIFYING_DIFFS,
)
from services.openai.init import create_openai_client
from services.openai.instructions import (
    SYSTEM_INSTRUCTION_FOR_AGENT,
    SYSTEM_INSTRUCTION_FOR_AGENT_REVIEW_DIFFS,
)
from utils.file_manager import clean_specific_lines, correct_hunk_headers, split_diffs
from services.github.github_manager import update_comment


def create_assistant() -> Assistant:
    client: OpenAI = create_openai_client()
    return client.beta.assistants.create(
        name="GitAuto: Automated Issue Resolver",
        instructions=SYSTEM_INSTRUCTION_FOR_AGENT,
        tools=[
            # {"type": "code_interpreter"},
            # {"type": "retrieval"},
            {"type": "function", "function": GET_REMOTE_FILE_CONTENT},
            {"type": "function", "function": COMMIT_MULTIPLE_CHANGES_TO_REMOTE_BRANCH},
            {"type": "function", "function": WHY_MODIFYING_DIFFS},
        ],
        model=OPENAI_MODEL_ID,
        timeout=TIMEOUT_IN_SECONDS,
    )


def create_thread_and_run(user_input: str) -> tuple[OpenAI, Assistant, Thread, Run]:
    """thread represents a conversation. 1 thread per 1 issue.
    Assistants API will manage the context window.
    https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client: OpenAI = create_openai_client()
    thread: Thread = client.beta.threads.create(timeout=TIMEOUT_IN_SECONDS)
    assistant: Assistant = create_assistant()
    run: Run = submit_message(
        client=client, assistant=assistant, thread=thread, user_message=user_input
    )
    return client, assistant, thread, run


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
    comment_url: str,
    token: str,
    new_branch: str,
) -> list[str]:
    # Create a message in the thread
    data: dict[str, str | list[str]] = {
        "owner": owner,
        "pr_body": pr_body,
        "repo": repo,
        "ref": ref,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issue_comments": issue_comments,
        "file_path": file_paths,
        "comment_url": comment_url,
        "new_branch": new_branch,
    }
    content: str = json.dumps(obj=data)
    # print(f"{data=}\n")

    # Run the assistant
    client, assistant, thread, run = create_thread_and_run(user_input=content)
    print(f"Thread is created: {thread.id}\n")
    print(f"Run is created: {run.id}\n")

    # Wait for the run to complete
    run: Run = wait_on_run(
        run=run, thread=thread, token=token, run_name="generate diffs"
    )

    # Get the response
    messages: SyncCursorPage[ThreadMessage] = get_response(thread=thread)
    messages_list = list(messages)
    if not messages_list:
        raise ValueError("No messages in the list.")
    latest_message: ThreadMessage = messages_list[0]
    if isinstance(latest_message.content[0], MessageContentText):
        value: str = latest_message.content[0].text.value
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

    update_comment(
        comment_url=comment_url,
        token=token,
        body="![X](https://progress-bar.dev/50/?title=Progress&width=800)\n50% Half way there!",
    )

    # Self review diff
    self_review_run = submit_message(
        client,
        assistant,
        thread,
        SYSTEM_INSTRUCTION_FOR_AGENT_REVIEW_DIFFS + json.dumps(output),
    )

    self_review_run: Run = wait_on_run(
        run=self_review_run, thread=thread, token=token, run_name="review diffs"
    )

    update_comment(
        comment_url=comment_url,
        token=token,
        body="![X](https://progress-bar.dev/70/?title=Progress&width=800)\n70% there! We're reviewing your new code changes!",
    )

    return output


def submit_message(
    client: OpenAI, assistant: Assistant, thread: Thread, user_message: str
) -> Run:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message,
        timeout=TIMEOUT_IN_SECONDS,
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant.id, timeout=TIMEOUT_IN_SECONDS
    )


def wait_on_run(run: Run, thread: Thread, token: str, run_name: str) -> Run:
    """https://cookbook.openai.com/examples/assistants_api_overview_python"""
    print(f"Run {run_name} status before loop: { run.status}")
    client: OpenAI = create_openai_client()
    while run.status not in OPENAI_FINAL_STATUSES:
        print(f"Run {run_name} status during loop: {run.status}")
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
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs_json,
                    timeout=TIMEOUT_IN_SECONDS,
                )
            except Exception as e:
                raise ValueError(f"Error: {e}") from e
        time.sleep(0.5)
    print(f"Run {run_name} status after loop: {run.status}")
    return run


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

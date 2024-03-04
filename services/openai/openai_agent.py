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
from openai.types.beta.threads.runs import RunStep

# Local imports
from config import (
    OPENAI_API_KEY, OPENAI_FINAL_STATUSES, OPENAI_MODEL_ID, OPENAI_ORG_ID, TIMEOUT_IN_SECONDS
)
from services.openai.functions import GET_REMOTE_FILE_CONTENT, functions
from services.openai.instructions import SYSTEM_INSTRUCTION
from utils.file_manager import clean_specific_lines, split_diffs

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)

# Create an assistant
assistant: Assistant = client.beta.assistants.create(
    name="GitAuto: Automated Issue Resolver",
    instructions=SYSTEM_INSTRUCTION,
    tools=[
        # {"type": "code_interpreter"},
        # {"type": "retrieval"},
        {"type": "function", "function": GET_REMOTE_FILE_CONTENT}
    ],
    model=OPENAI_MODEL_ID,
    timeout=TIMEOUT_IN_SECONDS
)
assistant_id: str = assistant.id
print(f"Assistant is created: {assistant_id}\n")


def create_thread_and_run(user_input: str) -> tuple[Thread, Run]:
    """ thread represents a conversation. 1 thread per 1 issue.
    Assistants API will manage the context window.
    https://cookbook.openai.com/examples/assistants_api_overview_python """
    thread: Thread = client.beta.threads.create(timeout=TIMEOUT_IN_SECONDS)
    run: Run = submit_message(thread=thread, user_message=user_input)
    return thread, run


def get_response(thread: Thread) -> SyncCursorPage[ThreadMessage]:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    return client.beta.threads.messages.list(
        thread_id=thread.id, order="desc", timeout=TIMEOUT_IN_SECONDS
    )


def run_assistant(
        file_paths: list[str],
        issue_title: str,
        issue_body: str,
        issue_comments: list[str],
        owner: str,
        ref: str,
        repo: str,
        token: str
        ) -> list[str]:

    # Create a message in the thread
    data: dict[str, str | list[str]] = {
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "issue_title": issue_title,
        "issue_body": issue_body,
        "issue_comments": issue_comments,
        "file_path": file_paths
    }
    content: str = json.dumps(obj=data)
    # print(f"{data=}\n")

    # Run the assistant
    thread, run = create_thread_and_run(user_input=content)
    print(f"Thread is created: {thread.id}\n")
    print(f"Run is created: {run.id}\n")

    # Wait for the run to complete
    run: Run = wait_on_run(run=run, thread=thread, token=token)

    # Get the steps
    run_steps: SyncCursorPage[RunStep] = client.beta.threads.runs.steps.list(
        thread_id=thread.id, run_id=run.id, order="desc", timeout=TIMEOUT_IN_SECONDS
    )
    for step in run_steps.data:
        step_details = step.step_details
        print(f"Step details: {step_details}\n")

    # Get the response
    messages: SyncCursorPage[ThreadMessage] = get_response(thread=thread)
    latest_message: ThreadMessage = list(messages)[0]
    if isinstance(latest_message.content[0], MessageContentText):
        value: str = latest_message.content[0].text.value
    else:
        raise ValueError("Last message content is not text.")
    print(f"Last message: {value}\n")

    # Clean the diff text and split it
    diff: str = clean_specific_lines(text=value)
    text_diffs: list[str] = split_diffs(diff_text=diff)
    for diff in text_diffs:
        print(f"Diff: {diff}\n")
    return text_diffs


def submit_message(thread: Thread, user_message: str) -> Run:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message, timeout=TIMEOUT_IN_SECONDS
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant_id, timeout=TIMEOUT_IN_SECONDS
    )


def wait_on_run(run: Run, thread: Thread, token: str) -> Run:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    print(f"Run status before loop: {run.status}")
    while run.status not in OPENAI_FINAL_STATUSES:
        print(f"Run status during loop: {run.status}")
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
            timeout=TIMEOUT_IN_SECONDS
        )

        # If the run requires action, call the function and run again with the output
        if run.status == "requires_action":
            print("Run requires action")
            try:
                tool_outputs: list[Any] = call_functions(
                    run=run,
                    funcs=functions,
                    token=token
                )
                tool_outputs_json: list[ToolOutput] = [{
                        "tool_call_id": tool_call.id, "output": json.dumps(obj=result)
                    } for tool_call, result in tool_outputs]
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs_json,
                    timeout=TIMEOUT_IN_SECONDS
                )
            except Exception as e:
                raise ValueError(f"Error: {e}") from e
        time.sleep(0.5)
    print(f"Run status after loop: {run.status}")
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

# Standard imports
import json
import time

# Third-party imports
from openai import OpenAI
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, ThreadMessage, MessageContentText
from openai.types.beta.threads.runs import RunStep

# Local imports
from config import OPENAI_API_KEY, OPENAI_MODEL_ID, OPENAI_ORG_ID
from services.openai.functions import get_remote_file_content
from services.openai.instructions import SYSTEM_INSTRUCTION
from utils.file_manager import split_diffs

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID)

# Create an assistant
assistant: Assistant = client.beta.assistants.create(
    name="GitAuto: Automated Issue Resolver",
    instructions=SYSTEM_INSTRUCTION,
    tools=[
        {"type": "code_interpreter"},
        {"type": "retrieval"},
        {"type": "function", "function": get_remote_file_content}
    ],
    model=OPENAI_MODEL_ID
)
assistant_id: str = assistant.id
print(f"Assistant is created: {assistant_id}\n")


def create_thread_and_run(user_input: str) -> tuple[Thread, Run]:
    """ thread represents a conversation. 1 thread per 1 issue. 
    Assistants API will manage the context window.
    https://cookbook.openai.com/examples/assistants_api_overview_python """
    thread: Thread = client.beta.threads.create()
    run: Run = submit_message(thread=thread, user_message=user_input)
    return thread, run


def get_response(thread: Thread) -> SyncCursorPage[ThreadMessage]:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")


def run_assistant(
        file_paths: list[str],
        issue_title: str,
        issue_body: str,
        issue_comments: list[str],
        owner: str,
        ref: str,
        repo: str,
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
    print(f"{data=}\n")

    # Run the assistant
    thread, run = create_thread_and_run(user_input=content)
    print(f"Thread is created: {thread.id}\n")
    print(f"Run is created: {run.id}\n")

    # Wait for the run to complete
    run: Run = wait_on_run(run=run, thread=thread)

    # Get the steps
    run_steps: SyncCursorPage[RunStep] = client.beta.threads.runs.steps.list(
        thread_id=thread.id, run_id=run.id, order="asc"
    )
    for step in run_steps.data:
        step_details = step.step_details
        print(json.dumps(obj=step_details, indent=2))

    # Get the response
    messages: SyncCursorPage[ThreadMessage] = get_response(thread=thread)
    latest_message: ThreadMessage = list(messages)[0]
    if isinstance(latest_message.content[0], MessageContentText):
        value: str = latest_message.content[0].text.value
    else:
        raise ValueError("Last message content is not text.")
    print(f"Last message: {value}\n")

    text_diffs: list[str] = split_diffs(diff_text=value)
    print(f"Text diffs: {text_diffs}\n")
    return text_diffs


def submit_message(thread: Thread, user_message: str) -> Run:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_message)
    return client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)


def wait_on_run(run: Run, thread: Thread) -> Run:
    """ https://cookbook.openai.com/examples/assistants_api_overview_python """
    print(f"Run status before loop: {run.status}")
    while run.status in ["queued", "in_progress"]:
        print(f"Run status during loop: {run.status}")
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    print(f"Run status after loop: {run.status}")
    return run

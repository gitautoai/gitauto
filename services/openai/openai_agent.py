# Standard imports
import json
import logging
import time

# Third-party imports
import openai
# from git import Repo
from openai.pagination import SyncCursorPage
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, ThreadMessage

# Local imports
from config import OPENAI_API_KEY, OPENAI_MODEL_ID, OPENAI_ORG_ID
# from services.github.github_manager import GitHubManager
from services.openai.functions import get_remote_file_content
from services.openai.instructions import SYSTEM_INSTRUCTION
from utils.logging import pretty_print


class OpenAIAgent:
    def __init__(self) -> None:
        openai.api_key = OPENAI_API_KEY
        openai.organization = OPENAI_ORG_ID
        logging.getLogger(name="openai").setLevel(level=logging.WARNING)

    def run_assistant(
            self,
            file_paths: list[str],
            issue_title: str,
            issue_body: str,
            issue_comments: list[str],
            owner: str,
            ref: str,
            repo: str,
            ) -> None:

        # Create an assistant
        assistant: Assistant = openai.beta.assistants.create(
            name="GitAuto: Automated Issue Resolver",
            instructions=SYSTEM_INSTRUCTION,
            tools=[get_remote_file_content],
            model=OPENAI_MODEL_ID
        )
        print(f"Assistant is created: {assistant.id}\n")
        # print(f"Assistant Object: {assistant}")

        # thread represents a conversation. 1 thread per 1 issue.
        # Assistants API will manage the context window.
        thread: Thread = openai.beta.threads.create()
        print(f"Thread is created: {thread.id}\n")
        print(f"Thread Object: {thread}\n")

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

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content
        )
        print(f"Message created in thread: {thread.id}\n")

        # Run the assistant
        run: Run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        print(f"Run is created: {run.id}\n")

        run = self.wait_on_run(run=run, thread=thread)
        messages: SyncCursorPage[ThreadMessage] = openai.beta.threads.messages.list(thread_id=thread.id, order="desc")
        # print(f"Messages: {messages}\n")
        pretty_print(messages=messages)
        # Apply changes to the repository

    def wait_on_run(self, run: Run, thread: Thread) -> Run:
        print(f"Run status before loop: {run.status}")
        while run.status in ["queued", "in_progress"]:
            # print(f"Run status during loop: {run.status}")
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        print(f"Run status after loop: {run.status}")
        return run

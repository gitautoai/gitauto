import os
import shlex

from anthropic.types import ToolUnionParam

from constants.shell import ALLOWED_PREFIXES, PATH_RESTRICTED_COMMANDS
from services.slack.slack_notify import slack_notify
from services.types.base_args import BaseArgs
from utils.command.run_subprocess import run_subprocess
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Output longer than this is truncated
INLINE_OUTPUT_LIMIT = 2_000

RUN_COMMAND: ToolUnionParam = {
    "name": "run_command",
    "description": (
        "Run a read-only shell command to look up package versions, dependencies, or system info. "
        "Allowed: npm (view/list/outdated/search), yarn (info/list/why), "
        "composer (show/outdated), pip (show/list/index), node -v, php -v/-m, date. "
        "Use this instead of fetching HTML pages for package version lookups."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to run (e.g. 'npm view @circleci/node version').",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    },
    "strict": True,
}


@handle_exceptions(default_return_value=None, raise_on_error=False)
def run_command(base_args: BaseArgs, command: str, **_kwargs):
    if not any(command.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        logger.info("Command blocked: %s", command)
        thread_ts = base_args.get("slack_thread_ts")
        slack_notify(f"⛔ Blocked command: `{command}`", thread_ts)
        return f"Command not allowed. Allowed prefixes: {', '.join(ALLOWED_PREFIXES)}"

    logger.info("Running command: %s", command)
    args = shlex.split(command)

    # For file-access commands, all path arguments must resolve under /tmp
    if args[0] in PATH_RESTRICTED_COMMANDS:
        for arg in args[1:]:
            if arg.startswith("-"):
                continue
            resolved = os.path.realpath(arg)
            if not resolved.startswith("/tmp"):
                logger.info("Path blocked: %s resolves to %s", arg, resolved)
                thread_ts = base_args.get("slack_thread_ts")
                slack_notify(
                    f"⛔ Blocked path: `{command}` (resolved to `{resolved}`)",
                    thread_ts,
                )
                return f"Path not allowed: {arg}. File access is restricted to /tmp."
    try:
        result = run_subprocess(args=args, cwd="/tmp")
    except ValueError as e:
        logger.info("Command error: %s", e)
        return str(e)

    output = result.stdout
    logger.info("Command completed: %s, len=%d", command, len(output))

    if len(output) > INLINE_OUTPUT_LIMIT:
        logger.info("Large output truncated: %s (%d chars)", command, len(output))
        thread_ts = base_args.get("slack_thread_ts")
        slack_notify(f"🖥️ Command: `{command}` (truncated)", thread_ts)
        return f"{output[:INLINE_OUTPUT_LIMIT]}\n\n... (truncated, showing {INLINE_OUTPUT_LIMIT:,} of {len(output):,} chars)"

    thread_ts = base_args.get("slack_thread_ts")
    slack_notify(f"🖥️ Command: `{command}`", thread_ts)
    return output

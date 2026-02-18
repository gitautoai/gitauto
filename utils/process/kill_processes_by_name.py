import os
import signal

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def kill_processes_by_name(name: str):
    """/proc is a Linux-only virtual filesystem (kernel-generated, always at /proc).
    On Lambda (Linux), this scans running processes and kills matching ones.
    On macOS (local dev), /proc doesn't exist, so @handle_exceptions catches FileNotFoundError and returns None.
    """
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue

        cmdline = read_local_file(
            file_path=os.path.join(entry, "cmdline"), base_dir="/proc"
        )
        if cmdline and name in cmdline:
            os.kill(int(entry), signal.SIGTERM)
            logger.info("Killed lingering %s process %s", name, entry)

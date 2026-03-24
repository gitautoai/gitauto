import os
import signal
import time

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def kill_processes_by_name(name: str):
    """/proc is a Linux-only virtual filesystem (kernel-generated, always at /proc).
    On Lambda (Linux), this scans running processes and kills matching ones.
    On macOS (local dev), /proc doesn't exist, so @handle_exceptions catches FileNotFoundError and returns None.
    """
    killed_pids: list[int] = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue

        cmdline = read_local_file(
            file_path=os.path.join(entry, "cmdline"), base_dir="/proc"
        )
        if cmdline and name in cmdline:
            pid = int(entry)
            os.kill(pid, signal.SIGKILL)
            killed_pids.append(pid)
            logger.info("Killed lingering %s process %s", name, entry)

    # Wait for killed processes to fully die so ports are released.
    # Without this, MongoMemoryServer fails with "Instance failed to start" because the port from the previous run is still bound.
    for pid in killed_pids:
        for _ in range(20):
            if not os.path.exists(f"/proc/{pid}"):
                break
            time.sleep(0.1)
        else:
            logger.warning("Process %d still alive after 2s", pid)

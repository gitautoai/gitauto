import os

# Local imports
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# https://www.freedesktop.org/software/systemd/man/os-release.html
_OS_RELEASE_PATH = "/etc/os-release"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def read_os_release_pretty_name():
    """Return /etc/os-release PRETTY_NAME (e.g., "Amazon Linux 2023"), or None on macOS / missing key."""
    if not os.path.exists(_OS_RELEASE_PATH):
        logger.info("read_os_release_pretty_name: %s not present", _OS_RELEASE_PATH)
        return None

    logger.info("read_os_release_pretty_name: reading %s", _OS_RELEASE_PATH)
    with open(_OS_RELEASE_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("PRETTY_NAME="):
                logger.debug(
                    "read_os_release_pretty_name: skipping non-PRETTY_NAME line"
                )
                continue
            value = line.split("=", 1)[1].strip()
            # PRETTY_NAME may be quoted (POSIX shell-style). Strip outer single or double quotes if present.
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                logger.info("read_os_release_pretty_name: stripping outer quotes")
                value = value[1:-1]
            if not value:
                logger.info(
                    "read_os_release_pretty_name: PRETTY_NAME present but empty"
                )
                return None
            logger.info("read_os_release_pretty_name: extracted %s", value)
            return value

    logger.info(
        "read_os_release_pretty_name: PRETTY_NAME line not found in %s",
        _OS_RELEASE_PATH,
    )
    return None

import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# ~12K tokens. Logs larger than this are saved to file instead of embedded in the initial message.
MAX_INLINE_LOG_CHARS = 50_000
CI_LOG_PATH = ".gitauto/ci_error_log.txt"


@handle_exceptions(default_return_value=None, raise_on_error=False)
def save_ci_log_to_file(clone_dir: str, cleaned_log: str):
    gitauto_dir = os.path.join(clone_dir, ".gitauto")
    os.makedirs(gitauto_dir, exist_ok=True)
    full_path = os.path.join(clone_dir, CI_LOG_PATH)
    with open(full_path, "w", encoding=UTF8) as f:
        f.write(cleaned_log)
    logger.info("Saved CI log (%d chars) to %s", len(cleaned_log), CI_LOG_PATH)

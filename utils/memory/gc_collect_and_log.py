import gc

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger
from utils.memory.get_rss_mb import get_rss_mb


@handle_exceptions(default_return_value=None, raise_on_error=False)
def gc_collect_and_log():
    before_mb = get_rss_mb()
    collected = gc.collect()
    after_mb = get_rss_mb()
    logger.info(
        "gc: collected=%d rss_before=%.1fMB rss_after=%.1fMB",
        collected,
        before_mb,
        after_mb,
    )

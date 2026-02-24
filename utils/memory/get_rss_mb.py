import platform
import resource

from utils.error.handle_exceptions import handle_exceptions

# macOS returns bytes, Linux returns KB
_IS_MACOS = platform.system() == "Darwin"


@handle_exceptions(default_return_value=0.0, raise_on_error=False)
def get_rss_mb():
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if _IS_MACOS:
        return ru_maxrss / (1024 * 1024)
    return ru_maxrss / 1024

import os
import shutil

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

# Common config template suffixes in PHP, Node.js, and other ecosystems
# e.g., .env.example → .env, preference.inc.default → preference.inc
_TEMPLATE_SUFFIXES = (".default", ".example", ".sample")


@handle_exceptions(default_return_value=None, raise_on_error=False)
def copy_config_templates(clone_dir: str):
    copied = 0
    for root, _dirs, files in os.walk(clone_dir):
        # Skip dependency directories
        basename = os.path.basename(root)
        if basename in ("node_modules", "vendor", "vendor-bin", ".git"):
            _dirs[:] = []
            continue

        for filename in files:
            for suffix in _TEMPLATE_SUFFIXES:
                if not filename.endswith(suffix):
                    continue

                template_path = os.path.join(root, filename)
                target_path = template_path[: -len(suffix)]
                if os.path.exists(target_path):
                    rel_path = os.path.relpath(target_path, clone_dir)
                    logger.info("Config template skip: %s already exists", rel_path)
                    continue

                shutil.copy2(template_path, target_path)
                rel_path = os.path.relpath(target_path, clone_dir)
                logger.info("Copied config template: %s", rel_path)
                copied += 1
    if copied:
        logger.info("Copied %d config template(s)", copied)

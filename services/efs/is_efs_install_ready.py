import asyncio

from constants.efs import EFS_TIMEOUT_SECONDS
from services.efs.get_efs_dir import get_efs_dir
from services.efs.start_async_install_on_efs import install_tasks
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def is_efs_install_ready(owner: str, repo: str, name: str = "node"):
    efs_dir = get_efs_dir(owner, repo)
    install_task = install_tasks.get(efs_dir, {}).get(name)

    if not install_task:
        logger.warning("%s: No async install found", name)
        return False

    logger.info("%s: Waiting for async install to complete...", name)
    install_success = await asyncio.wait_for(install_task, timeout=EFS_TIMEOUT_SECONDS)

    if not install_success:
        logger.error("%s: Async install failed", name)
        return False

    logger.info("%s: Async install completed", name)
    return True

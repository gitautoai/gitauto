import asyncio
import logging

from services.efs.get_efs_dir import get_efs_dir
from services.efs.start_async_install_on_efs import install_tasks
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
async def is_efs_install_ready(
    owner: str, repo: str, name: str = "node", timeout: int = 60
):
    efs_dir = get_efs_dir(owner, repo)
    install_task = install_tasks.get(efs_dir, {}).get(name)

    if not install_task:
        logging.warning("%s: No async install found for %s/%s", name, owner, repo)
        return False

    print(f"{name}: Waiting for async install to complete...")
    install_success = await asyncio.wait_for(install_task, timeout=timeout)

    if not install_success:
        logging.warning("%s: Async install failed for %s/%s", name, owner, repo)
        return False

    print(f"{name}: Async install completed for {owner}/{repo}")
    return True

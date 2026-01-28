import asyncio
from collections import defaultdict

from services.efs.get_efs_dir import get_efs_dir
from services.github.types.github_types import BaseArgs
from services.node.install_node_packages import install_node_packages
from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

_INSTALLERS = [
    ("node", install_node_packages),
    # ("python", install_python_packages),
    # ("php", install_php_packages),
]

# install_tasks example:
# {
#   "/mnt/efs/owner1/repo1": {"node": Task[bool], "python": Task[bool]},
#   "/mnt/efs/owner2/repo2": {"php": Task[bool]}
# }
install_tasks: defaultdict[str, dict[str, asyncio.Task[bool]]] = defaultdict(dict)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def start_async_install_on_efs(base_args: BaseArgs):
    owner = base_args["owner"]
    owner_id = base_args["owner_id"]
    repo = base_args["repo"]
    token = base_args["token"]
    base_branch = base_args["base_branch"]
    efs_dir = get_efs_dir(owner, repo)

    for name, func in _INSTALLERS:
        if name in install_tasks[efs_dir]:
            logger.info("%s: Found existing install task", name)
            task = install_tasks[efs_dir][name]
            if task.done():
                exc = task.exception()
                if exc is None and task.result():
                    logger.info("%s: Reusing successful install", name)
                    continue
                logger.warning("%s: Retrying failed install", name)
                del install_tasks[efs_dir][name]
            else:
                logger.info("%s: Install already in progress", name)
                continue

        if name not in install_tasks[efs_dir]:
            # Don't await - runs in background, checked later by is_efs_install_ready()
            task = asyncio.create_task(
                func(owner, owner_id, repo, base_branch, token, efs_dir)
            )
            install_tasks[efs_dir][name] = task
            logger.info("%s: Started async installation", name)

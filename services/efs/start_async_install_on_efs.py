import asyncio
from collections import defaultdict

from services.efs.get_efs_dir import get_efs_dir
from services.github.types.github_types import BaseArgs
from services.node.install_node_packages import install_node_packages
from utils.error.handle_exceptions import handle_exceptions

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
    clone_dir = base_args.get("clone_dir")
    efs_dir = get_efs_dir(owner, repo)

    for name, func in _INSTALLERS:
        if name in install_tasks[efs_dir]:
            print(f"{name}: Found existing install task for {owner}/{repo}")
            task = install_tasks[efs_dir][name]
            if task.done():
                try:
                    if task.result():
                        print(f"{name}: Reusing successful install for {owner}/{repo}")
                        continue
                except Exception:
                    pass

                print(f"{name}: Retrying failed install for {owner}/{repo}")
                del install_tasks[efs_dir][name]
            else:
                print(f"{name}: Install already in progress for {owner}/{repo}")
                continue

        if name not in install_tasks[efs_dir]:
            task = asyncio.create_task(
                func(owner, owner_id, repo, base_branch, token, efs_dir, clone_dir)
            )
            install_tasks[efs_dir][name] = task
            print(f"{name}: Started async installation for {owner}/{repo}")

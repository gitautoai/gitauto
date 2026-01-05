from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor

from services.efs.get_efs_dir import get_efs_dir
from services.github.types.github_types import BaseArgs
from services.node.install_node_packages import install_node_packages
from utils.error.handle_exceptions import handle_exceptions

_INSTALLERS = [
    ("node", install_node_packages),
    # ("python", install_python_packages),
    # ("php", install_php_packages),
]

_executor = ThreadPoolExecutor(max_workers=len(_INSTALLERS))

# install_futures example:
# {
#   "/mnt/efs/owner1/repo1": {"node": Future[bool], "python": Future[bool]},
#   "/mnt/efs/owner2/repo2": {"php": Future[bool]}
# }
install_futures: defaultdict[str, dict[str, Future[bool]]] = defaultdict(dict)


@handle_exceptions(default_return_value=None, raise_on_error=False)
def start_async_install_on_efs(base_args: BaseArgs):
    owner = base_args["owner"]
    owner_id = base_args["owner_id"]
    repo = base_args["repo"]
    token = base_args["token"]
    new_branch = base_args["new_branch"]
    efs_dir = get_efs_dir(owner, repo)

    for name, func in _INSTALLERS:
        if name in install_futures[efs_dir]:
            print(f"{name}: Found existing install future for {owner}/{repo}")
            future = install_futures[efs_dir][name]
            if future.done():
                if future.result(timeout=0):
                    print(f"{name}: Reusing successful install for {owner}/{repo}")
                    continue

                print(f"{name}: Retrying failed install for {owner}/{repo}")
                del install_futures[efs_dir][name]
            else:
                print(f"{name}: Install already in progress for {owner}/{repo}")
                continue

        if name not in install_futures[efs_dir]:
            future = _executor.submit(
                func, owner, owner_id, repo, new_branch, token, efs_dir
            )
            install_futures[efs_dir][name] = future
            print(f"{name}: Started async installation for {owner}/{repo}")

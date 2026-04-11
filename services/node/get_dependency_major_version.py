import json

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_dependency_major_version(clone_dir: str, package_name: str):
    pkg_content = read_local_file("package.json", base_dir=clone_dir)
    if not pkg_content:
        logger.info("No package.json found in %s", clone_dir)
        return None

    pkg = json.loads(pkg_content)
    if not isinstance(pkg, dict):
        logger.info("package.json is not a dict in %s", clone_dir)
        return None
    for deps_key in ("devDependencies", "dependencies"):
        deps = pkg.get(deps_key)
        if not isinstance(deps, dict):
            continue
        version_spec = deps.get(package_name)
        if not isinstance(version_spec, str) or not version_spec:
            continue
        return int(version_spec.lstrip("^~>=< ").split(".")[0])

    logger.info("%s not found in package.json dependencies", package_name)
    return None

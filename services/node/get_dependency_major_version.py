import json
import os

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
        logger.info("%s %s found in %s", package_name, version_spec, deps_key)
        return int(version_spec.lstrip("^~>=< ").split(".")[0])

    # Check transitive dep: package may be pulled in by another dep (e.g. mongodb-memory-server via @shelf/jest-mongodb)
    transitive_pkg_path = os.path.join("node_modules", package_name, "package.json")
    transitive_content = read_local_file(transitive_pkg_path, base_dir=clone_dir)
    if transitive_content:
        transitive_pkg = json.loads(transitive_content)
        if isinstance(transitive_pkg, dict):
            version_spec = transitive_pkg.get("version")
            if isinstance(version_spec, str) and version_spec:
                logger.info(
                    "%s %s found as transitive dep in node_modules",
                    package_name,
                    version_spec,
                )
                return int(version_spec.split(".")[0])

    logger.info("%s not found in package.json or node_modules", package_name)
    return None

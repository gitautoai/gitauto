import json

from constants.node import FALLBACK_NODE_VERSION
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file
from utils.logging.logging_config import logger
from utils.versions.extract_max_major_from_constraint import (
    extract_max_major_from_constraint,
)
from utils.versions.parse_major_version import parse_major_version


@handle_exceptions(default_return_value=FALLBACK_NODE_VERSION, raise_on_error=False)
def detect_node_version(clone_dir: str):
    """Detect the Node.js major version from repo config files. Returns e.g. '22'."""
    # 1. Check .nvmrc
    nvmrc = read_local_file(".nvmrc", base_dir=clone_dir)
    if isinstance(nvmrc, str):
        parsed = parse_major_version(nvmrc.strip())
        if parsed:
            logger.info("node: Detected Node %s from .nvmrc", parsed)
            return parsed

    # 2. Check .node-version
    node_version_file = read_local_file(".node-version", base_dir=clone_dir)
    if isinstance(node_version_file, str):
        parsed = parse_major_version(node_version_file.strip())
        if parsed:
            logger.info("node: Detected Node %s from .node-version", parsed)
            return parsed

    # 3. Check package.json engines.node
    package_json = read_local_file("package.json", base_dir=clone_dir)
    if isinstance(package_json, str):
        try:
            data = json.loads(package_json)
        except (json.JSONDecodeError, TypeError):
            data = None

        engines = data.get("engines") if isinstance(data, dict) else None
        node_constraint = engines.get("node") if isinstance(engines, dict) else None
        if isinstance(node_constraint, str):
            parsed = extract_max_major_from_constraint(node_constraint)
            if parsed:
                logger.info("node: Detected Node %s from package.json engines", parsed)
                return parsed

    logger.info(
        "node: No Node version specified, defaulting to %s", FALLBACK_NODE_VERSION
    )
    return FALLBACK_NODE_VERSION

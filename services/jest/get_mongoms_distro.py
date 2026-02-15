import json

from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_local_file import read_local_file


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_mongoms_distro(clone_dir: str):
    """Lambda runs on Amazon Linux 2023. MongoDB < 7.0 has no amazon2023 binary,
    so override distro to download the Ubuntu binary (glibc-compatible).
    MongoDB 7.0+ has native amazon2023 binaries, so let auto-detection work."""
    pkg_content = read_local_file("package.json", clone_dir)
    if not pkg_content:
        return None

    pkg = json.loads(pkg_content)
    if not isinstance(pkg, dict):
        return None

    config = pkg.get("config")
    if not isinstance(config, dict):
        return None

    mongoms = config.get("mongodbMemoryServer")
    if not isinstance(mongoms, dict):
        return None

    mongoms_version = mongoms.get("version")
    if isinstance(mongoms_version, str) and int(mongoms_version.split(".")[0]) < 7:
        # Hardcoded because MongoMemoryServer has no API to discover compatible distros.
        # Ubuntu 22.04 (glibc 2.35) is binary-compatible with Amazon Linux 2023 (glibc 2.34).
        return "ubuntu-22.04"

    return None

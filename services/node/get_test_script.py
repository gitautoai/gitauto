import json
import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_test_script(clone_dir: str):
    """Get test script from package.json, or None if not found."""
    package_json_path = os.path.join(clone_dir, "package.json")
    if not os.path.exists(package_json_path):
        return None

    with open(package_json_path, encoding=UTF8) as f:
        package_json = json.load(f)

    if not isinstance(package_json, dict):
        return None

    scripts = package_json.get("scripts", {})
    if not isinstance(scripts, dict):
        return None

    test_script = scripts.get("test")
    if isinstance(test_script, str) and test_script:
        return test_script

    return None

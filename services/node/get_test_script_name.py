import json
import os

from config import UTF8
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=(None, ""), raise_on_error=False)
def get_test_script_name(clone_dir: str):
    """Get the best test script name and value from package.json.

    Returns (script_name, script_value) or (None, "") if not found.
    Prefers "test:unit" over "test" because we only run unit tests.
    The script_value is needed to determine the actual runner (jest vs vitest)
    because the installed binary may differ from what the script invokes.
    """
    package_json_path = os.path.join(clone_dir, "package.json")
    if not os.path.exists(package_json_path):
        return None, ""

    with open(package_json_path, encoding=UTF8) as f:
        package_json = json.load(f)

    if not isinstance(package_json, dict):
        return None, ""

    scripts = package_json.get("scripts", {})
    if not isinstance(scripts, dict):
        return None, ""

    # Prefer "test:unit" because we only run unit tests
    test_unit = scripts.get("test:unit")
    if isinstance(test_unit, str) and test_unit:
        return "test:unit", test_unit

    test_script = scripts.get("test")
    if isinstance(test_script, str) and test_script:
        return "test", test_script

    return None, ""

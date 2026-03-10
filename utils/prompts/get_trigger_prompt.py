from constants.triggers import Trigger
from utils.error.handle_exceptions import handle_exceptions
from utils.files.read_xml_file import read_xml_file


@handle_exceptions(default_return_value=None, raise_on_error=False)
def get_trigger_prompt(trigger: Trigger):
    base_path = "utils/prompts/triggers"
    trigger_files = {
        "dashboard": f"{base_path}/pr.xml",
        "schedule": f"{base_path}/pr.xml",
        "pr_comment": f"{base_path}/review.xml",
        "pr_file_review": f"{base_path}/review.xml",
        "pr_review": f"{base_path}/review.xml",
        "test_failure": f"{base_path}/check_run.xml",
    }

    if trigger in trigger_files:
        return read_xml_file(trigger_files[trigger])
    return None

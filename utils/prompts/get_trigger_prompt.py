from services.supabase.usage.insert_usage import Trigger
from utils.files.read_xml_file import read_xml_file


def get_trigger_prompt(trigger: Trigger):
    base_path = "utils/prompts/triggers"
    trigger_files = {
        "issue_comment": f"{base_path}/issue.xml",
        "issue_label": f"{base_path}/issue.xml",
        "test_failure": f"{base_path}/check_run.xml",
        "review_comment": f"{base_path}/review.xml",
        "pr_checkbox": f"{base_path}/pr_checkbox.xml",
        "pr_merge": f"{base_path}/pr_merge.xml",
    }

    if trigger in trigger_files:
        return read_xml_file(trigger_files[trigger])
    return None

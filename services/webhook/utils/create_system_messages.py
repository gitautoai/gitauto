import json

from services.supabase.repositories.get_repository import RepositorySettings
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=[], raise_on_error=False)
def create_system_messages(repo_settings: RepositorySettings):
    system_messages = []

    if not repo_settings:
        return system_messages

    # Add structured rules first
    structured_rules = repo_settings.get("structured_rules")
    if structured_rules:
        structured_content = "\n".join(f"{k}: {v}" for k, v in structured_rules.items())
        system_messages.append(
            {
                "role": "system",
                "content": f"## Structured Repository Rules:\n\n{structured_content}",
            }
        )

    # Add free-format repository rules after
    repo_rules = repo_settings.get("repo_rules")
    if repo_rules and repo_rules.strip():
        system_messages.append(
            {"role": "system", "content": f"## Repository Rules:\n\n{repo_rules}"}
        )

    if system_messages:
        print(
            f"\nSystem messages:\n{json.dumps(system_messages[0]['content'], indent=2)}"
        )
    return system_messages

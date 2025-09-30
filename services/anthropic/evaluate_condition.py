from config import ANTHROPIC_MODEL_ID_45
from services.anthropic.client import claude
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def evaluate_condition(
    content: str,
    system_prompt: str,
    max_tokens: int = 100,
):
    if not content or not system_prompt:
        return False

    response = claude.messages.create(
        model=ANTHROPIC_MODEL_ID_45,
        max_tokens=max_tokens,
        temperature=0,
        system=f"""{system_prompt}

Respond with ONLY the word TRUE or FALSE. Nothing else.""",
        messages=[{"role": "user", "content": content}],
    )

    # Parse the response
    first_content = response.content[0]
    response_text = getattr(first_content, "text", "").strip().lower()

    # Simple parsing - just check for true or false
    if "true" in response_text:
        return True

    if "false" in response_text:
        return False

    return False

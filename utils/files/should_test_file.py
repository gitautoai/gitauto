from services.anthropic.evaluate_condition import evaluate_condition
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def should_test_file(file_path: str, content: str) -> bool:
    system_prompt = """You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests."""

    result = evaluate_condition(
        content=f"File path: {file_path}\n\nContent:\n{content}",
        system_prompt=system_prompt,
    )

    # Default to False if evaluation fails (avoid generating garbage)
    return bool(result) if result is not None else False

from services.anthropic.evaluate_condition import evaluate_condition
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def should_test_file(file_path: str, content: str) -> bool:
    system_prompt = """You are a very experienced senior engineer. Look at this code and decide if it needs unit tests.

Be practical and strict - only return TRUE if the code has actual logic worth testing.

Return FALSE for trivial code that doesn't need tests."""

    result = evaluate_condition(
        content=f"File path: {file_path}\n\nContent:\n{content}",
        system_prompt=system_prompt,
    )

    # Default to False if evaluation fails (avoid generating garbage)
    return bool(result) if result is not None else False

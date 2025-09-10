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

    # Ensure we always return a boolean
    # Handle None case explicitly
    if result is None:
        return False
    
    # Convert any truthy/falsy value to boolean
    return True if result else False
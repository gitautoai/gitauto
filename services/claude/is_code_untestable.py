from services.claude.evaluate_condition import EvaluationResult, evaluate_condition
from utils.formatting.format_with_line_numbers import format_content_with_line_numbers

SYSTEM_PROMPT = """You are a code analysis expert. Determine if the given uncovered code is UNTESTABLE or DEAD CODE that should be removed.

Code is UNTESTABLE or DEAD (return true) if:
1. Async error handlers in React/Vue/Angular event handlers (onClick, onSubmit) that throw errors - become unhandled promise rejections
2. Error throws inside callbacks that test frameworks cannot catch
3. Code paths only executing in specific runtime environments tests cannot simulate
4. Race condition handlers depending on timing
5. DEAD CODE: Logically unreachable code due to earlier conditions already handling the case (e.g., checking `x === ''` after `!x` already returned, since empty string is falsy)

Code is TESTABLE (return false) if:
1. Can be tested by mocking dependencies
2. Can be tested by spying on console.error/console.log
3. Can be tested by checking UI state changes
4. Simply missing test coverage but technically testable

Return:
- result: true if genuinely untestable due to testing library constraints OR if dead/unreachable code that should be removed
- reason: include which line numbers are untestable/dead and why
"""


def is_code_untestable(
    file_path: str,
    file_content: str,
    uncovered_lines: str | None = None,
    uncovered_functions: str | None = None,
    uncovered_branches: str | None = None,
):
    parts: list[str] = []

    # Extract uncovered lines from file content
    if uncovered_lines:
        line_nums = [int(n.strip()) for n in uncovered_lines.split(",") if n.strip()]
        lines = file_content.splitlines()
        extracted: list[str] = []
        for num in line_nums:
            if 0 < num <= len(lines):
                extracted.append(f"{num}: {lines[num - 1]}")
        if extracted:
            parts.append(f"Uncovered lines:\n```\n{"\n".join(extracted)}\n```")

    if uncovered_functions:
        parts.append(f"Uncovered functions: {uncovered_functions}")

    if uncovered_branches:
        parts.append(f"Uncovered branches: {uncovered_branches}")

    if not parts:
        return EvaluationResult(False, "No uncovered code provided")

    numbered_file = format_content_with_line_numbers(
        file_path=file_path, content=file_content
    )

    content = f"""{"\n".join(parts)}

{numbered_file}

Is this code untestable due to testing library constraints?"""

    return evaluate_condition(content=content, system_prompt=SYSTEM_PROMPT)

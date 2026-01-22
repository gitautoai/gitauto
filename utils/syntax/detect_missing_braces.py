import re
from typing import TypedDict

from utils.error.handle_exceptions import handle_exceptions


class MissingBrace(TypedDict):
    block_start_line: int
    block_type: str
    insert_after_line: int
    missing: str


@handle_exceptions(default_return_value=[], raise_on_error=False)
def detect_missing_braces(content: str):
    lines = content.split("\n")
    # Match describe/test/it blocks with arrow function opening brace
    block_pattern = re.compile(r"^(\s*)(describe|test|it)\s*\(.*=>\s*\{\s*$")

    # Stack stores (line_number, block_type, indent_level) for unclosed blocks
    stack: list[tuple[int, str, int]] = []
    detected_pattern = "});"

    for i, line in enumerate(lines):
        block_match = block_pattern.match(line)
        if block_match:
            indent = len(block_match.group(1))
            block_type = block_match.group(2)
            stack.append((i, block_type, indent))

        stripped = line.strip()
        if stripped == "});":
            line_indent = len(line) - len(line.lstrip())
            # Pop matching block from stack (same indent = closes that block)
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][2] == line_indent:
                    stack.pop(j)
                    break

    results: list[MissingBrace] = []

    if not stack:
        return results

    for block_line, block_type, block_indent in stack:
        insert_after = block_line

        # Find last line before next block at same/lower indent or closing brace
        for i in range(block_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue

            line_indent = len(line) - len(line.lstrip())

            if line.strip() == "});" and line_indent <= block_indent:
                break

            next_block = block_pattern.match(line)
            if next_block and len(next_block.group(1)) <= block_indent:
                break

            insert_after = i

        # Skip trailing blank lines
        while insert_after > block_line and not lines[insert_after].strip():
            insert_after -= 1

        results.append(
            MissingBrace(
                block_start_line=block_line + 1,
                block_type=block_type,
                insert_after_line=insert_after + 1,
                missing=detected_pattern,
            )
        )

    return results

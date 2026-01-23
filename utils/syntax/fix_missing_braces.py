import re
from typing import TypedDict

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


class MissingBrace(TypedDict):
    block_start_line: int
    block_type: str
    insert_after_line: int
    missing: str


class FixResult(TypedDict):
    content: str
    fixes: list[MissingBrace]


@handle_exceptions(
    default_return_value={"content": "", "fixes": []}, raise_on_error=False
)
def fix_missing_braces(content: str) -> FixResult:
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

    if not stack:
        return FixResult(content=content, fixes=[])

    fixes: list[MissingBrace] = []
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

        fixes.append(
            MissingBrace(
                block_start_line=block_line + 1,
                block_type=block_type,
                insert_after_line=insert_after + 1,
                missing=detected_pattern,
            )
        )

    # Sort by insert_after_line descending so we insert from bottom-up
    # This prevents line number shifts from affecting earlier insertions
    sorted_fixes = sorted(fixes, key=lambda x: x["insert_after_line"], reverse=True)
    for fix in sorted_fixes:
        insert_idx = fix["insert_after_line"] - 1  # Convert to 0-indexed
        block_indent = len(lines[fix["block_start_line"] - 1]) - len(
            lines[fix["block_start_line"] - 1].lstrip()
        )
        closing_brace = " " * block_indent + fix["missing"]

        next_idx = insert_idx + 1
        if next_idx < len(lines) and not lines[next_idx].strip():
            check_idx = next_idx + 1
            while check_idx < len(lines) and not lines[check_idx].strip():
                check_idx += 1
            if check_idx < len(lines) and lines[check_idx].strip() == "});":
                logger.info(
                    "Replacing blank line %s with '%s' because blank followed by }); means Claude forgot to write });",
                    next_idx + 1,
                    closing_brace,
                )
                lines[next_idx] = closing_brace
            else:
                logger.info(
                    "Inserting '%s' after line %s because blank followed by code means it's spacing",
                    closing_brace,
                    insert_idx + 1,
                )
                lines.insert(next_idx, closing_brace)
        else:
            logger.info(
                "Inserting '%s' after line %s because next line is not blank",
                closing_brace,
                insert_idx + 1,
            )
            lines.insert(next_idx, closing_brace)

    return FixResult(content="\n".join(lines), fixes=fixes)

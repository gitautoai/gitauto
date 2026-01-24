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

    # Match const/let/var declarations with object literal opening brace
    const_pattern = re.compile(r"^(\s*)(const|let|var)\s+\w+\s*=\s*\{\s*$")

    # Stack stores (line_number, block_type, indent_level) for unclosed blocks
    block_stack: list[tuple[int, str, int]] = []

    # Separate stack for const/let/var object literals
    const_stack: list[tuple[int, str, int]] = []

    for i, line in enumerate(lines):
        block_match = block_pattern.match(line)
        if block_match:
            indent = len(block_match.group(1))
            block_type = block_match.group(2)
            block_stack.append((i, block_type, indent))

        const_match = const_pattern.match(line)
        if const_match:
            indent = len(const_match.group(1))
            const_type = const_match.group(2)
            # Check if there's an unclosed const at same indent - that one is missing };
            for j in range(len(const_stack) - 1, -1, -1):
                if const_stack[j][2] == indent:
                    logger.info(
                        "Found unclosed const at line %d before new const at line %d",
                        const_stack[j][0] + 1,
                        i + 1,
                    )
                    break
            const_stack.append((i, const_type, indent))

        stripped = line.strip()
        if stripped == "});":
            line_indent = len(line) - len(line.lstrip())
            # Pop matching block from block_stack (same indent = closes that block)
            for j in range(len(block_stack) - 1, -1, -1):
                if block_stack[j][2] == line_indent:
                    # Found matching }); - block is properly closed
                    block_stack.pop(j)
                    break

        if stripped == "};":
            line_indent = len(line) - len(line.lstrip())
            # Pop matching const from const_stack
            for j in range(len(const_stack) - 1, -1, -1):
                if const_stack[j][2] == line_indent:
                    # Found matching }; - const is properly closed
                    const_stack.pop(j)
                    break

    if not block_stack and not const_stack:
        logger.info(
            "No missing braces detected: block_stack=%s, const_stack=%s",
            block_stack,
            const_stack,
        )
        return FixResult(content=content, fixes=[])

    fixes: list[MissingBrace] = []

    # Process describe/test/it blocks
    for block_line, block_type, block_indent in block_stack:
        insert_after = block_line

        # Find last line before next block at same/lower indent or closing brace
        for i in range(block_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                # Skip blank lines
                continue

            line_indent = len(line) - len(line.lstrip())

            if line.strip() == "});" and line_indent <= block_indent:
                # Found closing brace at same/lower indent - stop searching
                break

            next_block = block_pattern.match(line)
            if next_block and len(next_block.group(1)) <= block_indent:
                # Found next block at same/lower indent - stop searching
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
                missing="});",
            )
        )

    # Process const/let/var object literals - find ones missing };
    # A const is unclosed if another const at same indent appears before its };
    for idx, (const_line, const_type, const_indent) in enumerate(const_stack):
        # Check if there's a later const at same indent (meaning this one is unclosed)
        next_const_line = None
        for j in range(idx + 1, len(const_stack)):
            if const_stack[j][2] == const_indent:
                # Found another const at same indent - current one is unclosed
                next_const_line = const_stack[j][0]
                break

        if next_const_line is None:
            # No following const at same indent - cannot detect if missing
            continue

        # Find the line right before the next const (skip blank lines going backwards)
        insert_after = next_const_line - 1
        while insert_after > const_line and not lines[insert_after].strip():
            insert_after -= 1

        fixes.append(
            MissingBrace(
                block_start_line=const_line + 1,
                block_type=const_type,
                insert_after_line=insert_after + 1,
                missing="};",
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

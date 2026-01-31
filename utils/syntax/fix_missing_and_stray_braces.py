import re
from typing import TypedDict

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


class MissingBrace(TypedDict):
    block_start_line: int
    block_type: str
    insert_after_line: int
    missing: str


class StrayBrace(TypedDict):
    removed_line: int
    brace_type: str
    removed_content: str


class FixResult(TypedDict):
    content: str
    fixes: list[MissingBrace | StrayBrace]


def _pop_from_stack(
    stack: list[tuple[int, str, int]],
    indent: int,
    current_line: int,
    stack_name: str | None,
):
    for j in range(len(stack) - 1, -1, -1):
        if stack[j][2] != indent:
            continue

        popped = stack.pop(j)
        if stack_name:
            logger.debug(
                "Line %d: pop %s from line %d",
                current_line + 1,
                stack_name,
                popped[0] + 1,
            )

        else:
            logger.debug(
                "Line %d: pop %s from line %d",
                current_line + 1,
                popped[1],
                popped[0] + 1,
            )
        return True

    return False


@handle_exceptions(
    default_return_value={"content": "", "fixes": []}, raise_on_error=False
)
def fix_missing_and_stray_braces(content: str):
    r"""
    Why pattern matching instead of bracket counting?
    Simple bracket counting (track all `{`, `}`, etc.) would be more universal,
    but requires a proper tokenizer to handle strings (`"{"`), comments (`// {`),
    regex (`/\{/`), and template literals. Pattern matching is simpler to implement
    and covers the common test file patterns we encounter.
    """
    lines = content.split("\n")
    # Match any function call with callback (arrow or regular function)
    # Also matches assignments like: simulateOn = jest.fn((event, fn) => {
    block_pattern = re.compile(
        r"^(\s*)(?:.*?(?:await\s+)?)?(\w+)\s*\(.*(?:=>\s*\{|function\s*\([^)]*\)\s*\{)\s*$"
    )

    # Match function call with object literal argument: something({ or something.method({
    # Also matches assignments like: const x = createMocks({
    # But NOT function declarations with destructured params: function name({
    obj_arg_pattern = re.compile(r"^(\s*)(?!.*\bfunction\b).*?(\w+)\s*\(\s*\{\s*$")

    # Match function call with array literal argument: something([ or something.method([
    arr_arg_pattern = re.compile(r"^(\s*)(\w+(?:\.\w+)*)\s*\(\s*\[\s*$")

    # Match const/let/var declarations with object literal opening brace
    const_pattern = re.compile(r"^(\s*)(const|let|var)\s+\w+\s*=\s*\{\s*$")

    # Stack stores (line_number, block_type, indent_level) for unclosed blocks
    block_stack: list[tuple[int, str, int]] = []

    # Stack for object literal arguments like mockReturnValue({ - tracked but not fixed
    obj_arg_stack: list[tuple[int, str, int]] = []

    # Stack for array literal arguments like mockReturnValue([
    arr_arg_stack: list[tuple[int, str, int]] = []

    # Track unclosed arr_args detected when a new one opens at same indent
    unclosed_arr_args: list[tuple[int, str, int, int]] = []

    # Separate stack for const/let/var object literals
    const_stack: list[tuple[int, str, int]] = []

    # Track stray ]); lines (orphan closing braces)
    stray_lines: list[int] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        line_indent = len(line) - len(line.lstrip())

        # Skip commented lines
        if stripped.startswith("//"):
            continue

        # Handle opening patterns
        block_match = block_pattern.match(line)
        if block_match:
            indent = len(block_match.group(1))
            block_type = block_match.group(2)
            if block_type == "async":
                logger.debug("Line %d: skip async keyword", i + 1)
            else:
                block_stack.append((i, block_type, indent))
                logger.debug(
                    "Line %d: push %s to block_stack (indent=%d)",
                    i + 1,
                    block_type,
                    indent,
                )
        elif obj_arg_pattern.match(line):
            obj_arg_stack.append((i, "obj_arg", line_indent))
            logger.debug(
                "Line %d: push obj_arg to obj_arg_stack (indent=%d)", i + 1, line_indent
            )
        elif arr_arg_match := arr_arg_pattern.match(line):
            func_name = arr_arg_match.group(2).split(".")[-1]
            if func_name == "each":
                logger.debug("Line %d: skip .each([ pattern", i + 1)
            else:
                for j in range(len(arr_arg_stack) - 1, -1, -1):
                    if arr_arg_stack[j][2] != line_indent:
                        continue
                    logger.info(
                        "Found unclosed arr_arg at line %d before new arr_arg at line %d",
                        arr_arg_stack[j][0] + 1,
                        i + 1,
                    )
                    prev_line, prev_type, prev_indent = arr_arg_stack.pop(j)
                    unclosed_arr_args.append((prev_line, prev_type, prev_indent, i))
                    break
                arr_arg_stack.append((i, func_name, line_indent))
                logger.debug(
                    "Line %d: push %s to arr_arg_stack (indent=%d)",
                    i + 1,
                    func_name,
                    line_indent,
                )

        const_match = const_pattern.match(line)
        if const_match:
            indent = len(const_match.group(1))
            const_type = const_match.group(2)
            for j in range(len(const_stack) - 1, -1, -1):
                if const_stack[j][2] != indent:
                    continue
                logger.info(
                    "Found unclosed const at line %d before new const at line %d",
                    const_stack[j][0] + 1,
                    i + 1,
                )
                break
            const_stack.append((i, const_type, indent))

        # Handle ]); closing for array arguments
        if stripped == "]);":
            if not _pop_from_stack(arr_arg_stack, line_indent, i, "arr_arg"):
                logger.debug("Line %d: stray ]); detected", i + 1)
                stray_lines.append(i)

        # Handle closing patterns - both }); and }) can close blocks
        # Also handle Jest timeout: }, 30000); or }, timeout); or }, { timeout: 10000 });
        # Also handle React useEffect: }, [dep1, dep2])
        # Also handle JSX callback: })}
        is_block_close = stripped in ("});", "})", "})}") or re.match(
            r"^\},\s*(?:\w+|\[.*\]|\{.*\})\)?;?$", stripped
        )
        if is_block_close:
            if _pop_from_stack(obj_arg_stack, line_indent, i, "obj_arg"):
                pass
            elif _pop_from_stack(block_stack, line_indent, i, None):
                pass
            elif stripped == "});":
                # Only mark as stray if previous non-blank line ends with ); or ;
                # This catches cases where GitAuto added an extra }); after a function call
                prev_idx = i - 1
                while prev_idx >= 0 and not lines[prev_idx].strip():
                    prev_idx -= 1
                if prev_idx >= 0:
                    prev_stripped = lines[prev_idx].strip()
                    if prev_stripped.endswith(");") or prev_stripped.endswith(";"):
                        logger.debug(
                            "Line %d: stray }); detected (prev ends with ;)", i + 1
                        )
                        stray_lines.append(i)

        if stripped in ("};", "}"):
            _pop_from_stack(const_stack, line_indent, i, "const")

    if (
        not block_stack
        and not const_stack
        and not arr_arg_stack
        and not unclosed_arr_args
        and not stray_lines
    ):
        logger.info(
            "No issues detected: block_stack=%s, const_stack=%s, arr_arg_stack=%s, "
            "unclosed_arr_args=%s, stray_lines=%s",
            block_stack,
            const_stack,
            arr_arg_stack,
            unclosed_arr_args,
            stray_lines,
        )
        return FixResult(content=content, fixes=[])

    fixes: list[MissingBrace | StrayBrace] = []

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

    # Process unclosed array arguments detected during first pass
    for arr_line, arr_type, _, next_arr_line in unclosed_arr_args:
        insert_after = next_arr_line - 1
        while insert_after > arr_line and not lines[insert_after].strip():
            insert_after -= 1

        fixes.append(
            MissingBrace(
                block_start_line=arr_line + 1,
                block_type=arr_type,
                insert_after_line=insert_after + 1,
                missing="]);",
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

    # Remove stray ]); and }); lines FIRST (process in reverse order to preserve line numbers)
    # This must happen before insertions to avoid line number shifts
    for stray_idx in sorted(stray_lines, reverse=True):
        removed_line = lines[stray_idx]
        logger.info(
            "Removing stray brace at line %d: '%s'", stray_idx + 1, removed_line
        )
        lines.pop(stray_idx)
        fixes.append(
            StrayBrace(
                removed_line=stray_idx + 1,
                brace_type="stray",
                removed_content=removed_line.strip(),
            )
        )

    # Adjust insert_after_line for fixes that come after removed stray lines
    for fix in fixes:
        if "insert_after_line" not in fix:
            continue
        for stray_idx in stray_lines:
            if fix["insert_after_line"] > stray_idx + 1:
                fix["insert_after_line"] -= 1

    # Filter to only MissingBrace items for insertion processing
    missing_fixes = [f for f in fixes if "insert_after_line" in f]

    # Sort by insert_after_line descending so we insert from bottom-up
    # This prevents line number shifts from affecting earlier insertions
    sorted_fixes = sorted(
        missing_fixes, key=lambda x: x["insert_after_line"], reverse=True
    )
    for fix in sorted_fixes:
        insert_idx = fix["insert_after_line"] - 1  # Convert to 0-indexed
        start_line = lines[fix["block_start_line"] - 1]
        block_indent = len(start_line) - len(start_line.lstrip())
        closing_brace = " " * block_indent + fix["missing"]
        next_idx = insert_idx + 1

        # Next line is not blank - just insert
        if next_idx >= len(lines) or lines[next_idx].strip():
            logger.info("Inserting '%s' after line %s", closing_brace, insert_idx + 1)
            lines.insert(next_idx, closing_brace)
            continue

        # Next line is blank - check if followed by });
        check_idx = next_idx + 1
        while check_idx < len(lines) and not lines[check_idx].strip():
            check_idx += 1

        # Blank followed by }); means Claude forgot to write }); - replace blank
        if check_idx < len(lines) and lines[check_idx].strip() == "});":
            logger.info(
                "Replacing blank line %s with '%s'", next_idx + 1, closing_brace
            )
            lines[next_idx] = closing_brace
            continue

        # Blank followed by code - insert after keeping spacing
        logger.info("Inserting '%s' after line %s", closing_brace, insert_idx + 1)
        lines.insert(next_idx, closing_brace)

    return FixResult(content="\n".join(lines), fixes=fixes)

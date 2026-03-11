import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger

HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@handle_exceptions(
    default_return_value=lambda diff_text: diff_text, raise_on_error=False
)
def fix_diff_hunk_counts(diff_text: str):
    lines = diff_text.split("\n")
    hunk_starts: list[int] = []
    for i, line in enumerate(lines):
        if HUNK_HEADER_RE.match(line):
            hunk_starts.append(i)

    if not hunk_starts:
        return diff_text

    # Strip trailing empty string from split (artifact of trailing newline)
    had_trailing_newline = lines and lines[-1] == ""
    if had_trailing_newline:
        lines.pop()

    for idx, hunk_line_idx in enumerate(hunk_starts):
        # Determine the range of body lines for this hunk
        body_start = hunk_line_idx + 1
        if idx + 1 < len(hunk_starts):
            body_end = hunk_starts[idx + 1]
        else:
            body_end = len(lines)

        # Walk backwards to exclude trailing non-diff lines (e.g. next file's diff/index headers)
        while body_end > body_start and not lines[body_end - 1].startswith(
            ("+", "-", " ", "\\")
        ):
            body_end -= 1

        # Count old (context + removal) and new (context + addition) lines
        old_count = 0
        new_count = 0
        for j in range(body_start, body_end):
            line = lines[j]
            if line.startswith("-"):
                old_count += 1
            elif line.startswith("+"):
                new_count += 1
            elif line.startswith(" "):
                # Context line counts toward both sides
                old_count += 1
                new_count += 1
            # Lines like "\ No newline at end of file" are ignored

        # Rebuild the hunk header with correct counts
        m = HUNK_HEADER_RE.match(lines[hunk_line_idx])
        if not m:
            continue
        original_header = lines[hunk_line_idx]
        start1 = m.group(1)
        start2 = m.group(3)
        # Preserve any trailing context after the closing @@
        after_header = lines[hunk_line_idx][m.end() :]
        lines[hunk_line_idx] = (
            f"@@ -{start1},{old_count} +{start2},{new_count} @@{after_header}"
        )
        if lines[hunk_line_idx] != original_header:
            logger.info(
                "Fixed hunk header: %s -> %s", original_header, lines[hunk_line_idx]
            )

    result = "\n".join(lines)
    if had_trailing_newline:
        result += "\n"
    return result

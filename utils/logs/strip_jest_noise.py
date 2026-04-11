import re

from utils.error.handle_exceptions import handle_exceptions
from utils.logging.logging_config import logger


@handle_exceptions(default_return_value=lambda log: log, raise_on_error=False)
def strip_jest_noise(log: str):
    """Strip noise from raw jest/vitest subprocess output.

    Removes JSON debug lines from console.log, passing test indicator lines,
    MongoDB download progress, PASS test suite sections, and ANSI color codes.
    """
    if not log:
        return log

    # Strip ANSI color codes first
    log = re.sub(r"\x1b\[[0-9;]*m", "", log)

    lines = log.splitlines()
    result: list[str] = []
    in_pass_section = False
    in_console_block = False
    in_coverage_table = False

    for line in lines:
        stripped = line.strip()

        # Track console.error/warn/log blocks — these are application noise, not test failures.
        # Blocks start with "  console.error" etc. and continue with indented content.
        if re.match(r"^console\.(error|warn|log)$", stripped):
            in_console_block = True
            continue
        if in_console_block:
            # Exit console block on structural lines (PASS/FAIL/● or summary or yarn info)
            if (
                stripped.startswith(("PASS ", "FAIL ", "● "))
                or re.match(
                    r"^(Test Suites:|Tests:|Snapshots:|Time:|Ran all)", stripped
                )
                or stripped.startswith(("info ", "warning "))
            ):
                in_console_block = False
            else:
                continue

        # Track PASS/FAIL sections to skip entire PASS blocks
        if stripped.startswith("PASS "):
            in_pass_section = True
            continue
        if stripped.startswith("FAIL "):
            in_pass_section = False

        # Exit PASS section on summary or error lines
        if in_pass_section:
            if re.match(
                r"^(Test Suites:|Tests:|Snapshots:|Time:|Ran all test suites|error Command )",
                stripped,
            ):
                in_pass_section = False
            else:
                continue

        # Skip coverage table (lines with | separators showing file-level coverage).
        # Coverage data is useless when tests fail — it's all 0% and can be 30K+ chars.
        # Table format: separator lines (------|), header (File | % Stmts), data rows.
        if re.match(r"^-+\|", stripped):
            in_coverage_table = True
            continue
        if in_coverage_table:
            if "|" in stripped and not stripped.startswith(
                ("Test Suites:", "Tests:", "error ")
            ):
                continue
            in_coverage_table = False

        # Skip JSON debug log lines from application console output
        if stripped.startswith("{") and stripped.endswith("}"):
            continue

        # Skip passing test indicator lines
        if re.search(r"[✓√]", stripped):
            continue

        # Skip MongoDB download progress
        if "Downloading MongoDB" in line:
            continue

        result.append(line)

    filtered = "\n".join(result)
    if log.endswith("\n") and not filtered.endswith("\n"):
        filtered += "\n"
    logger.info("Stripped jest noise from %d to %d chars", len(log), len(filtered))
    return filtered

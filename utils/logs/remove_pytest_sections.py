def remove_pytest_sections(log: str | None) -> str | None:
    """
    Remove pytest test session and warnings sections from logs while keeping failures.

    This function removes:
    - Test session header and test results (from "test session starts" until FAILURES/summary)
    - Warnings summary section
    - Coverage section

    But keeps:
    - FAILURES section
    - short test summary info section
    - Final summary line (e.g., "1 failed, 2616 passed...")
    """
    if log is None:
        return None

    if not log:
        return log

    lines = log.split("\n")
    filtered_lines = []
    skip = False
    in_session_section = False
    in_warnings_section = False
    in_coverage_section = False
    content_removed = False

    for line in lines:
        # Detect start of test session section
        if "test session starts" in line and "===" in line:
            in_session_section = True
            skip = True
            content_removed = True
            continue

        # Detect start of warnings summary section
        if "warnings summary" in line and "===" in line:
            in_warnings_section = True
            skip = True
            content_removed = True
            continue

        # Detect start of coverage section
        if "---------- coverage:" in line or "Coverage LCOV written" in line:
            in_coverage_section = True
            skip = True
            content_removed = True
            continue

        # Detect FAILURES section - this ends session/warnings sections
        if "FAILURES" in line and "===" in line:
            in_session_section = False
            in_warnings_section = False
            in_coverage_section = False
            skip = False
            # Add blank line before FAILURES if needed
            if filtered_lines and filtered_lines[-1].strip():
                filtered_lines.append("")

        # Detect short test summary info - this ends session/warnings/coverage sections
        if "short test summary info" in line and "===" in line:
            in_session_section = False
            in_warnings_section = False
            in_coverage_section = False
            skip = False
            # Add blank line before summary if needed
            if filtered_lines and filtered_lines[-1].strip():
                filtered_lines.append("")

        # Handle session section content - skip everything until we hit a marker
        if in_session_section:
            # Check if this line marks the end of session section
            if ("===" in line and
                ("FAILURES" in line or
                 "short test summary info" in line or
                 "warnings summary" in line)):
                # This line will be handled in the next iteration
                in_session_section = False
                skip = False
            else:
                # Still in session section, keep skipping
                skip = True

        # Handle warnings section content
        if in_warnings_section:
            # Check for end markers
            if "-- Docs:" in line or ("===" in line and ("FAILURES" in line or "short test summary info" in line)):
                in_warnings_section = False
                skip = False
                # Don't add the Docs line
                if "-- Docs:" in line:
                    continue

        # Handle coverage section content
        if in_coverage_section:
            # Coverage section ends at FAILURES or short test summary or final summary line
            if ("===" in line and ("FAILURES" in line or "short test summary info" in line)) or \
               ("failed" in line and "passed" in line and "in" in line and "s" in line):
                in_coverage_section = False
                skip = False
            else:
                skip = True

        # Add line if not skipping
        if not skip:
            filtered_lines.append(line)

    # Clean up excessive blank lines only if content was removed
    if content_removed:
        result_lines = []
        blank_count = 0

        for line in filtered_lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 1:  # Allow up to 1 blank line
                    result_lines.append(line)
            else:
                blank_count = 0
                result_lines.append(line)

        # Remove trailing blank lines
        while result_lines and result_lines[-1].strip() == "":
            result_lines.pop()

        return "\n".join(result_lines)

    return "\n".join(filtered_lines)

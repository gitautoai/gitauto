def remove_pytest_sections(log: str | None) -> str | None:
    """
    Remove pytest test session and warnings sections from logs while keeping failures.

    This function removes:
    - Test session header and test results (from "test session starts" until FAILURES/summary)
    - Warnings summary section (can appear before or after FAILURES)
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
    skip_mode = None  # Can be 'session', 'warnings', 'coverage', or None
    content_removed = False

    for i, line in enumerate(lines):
        # Check if we should start skipping
        if skip_mode is None:
            # Detect start of test session section
            if "test session starts" in line and "===" in line:
                skip_mode = 'session'
                content_removed = True
                continue

            # Detect start of warnings summary section
            if "warnings summary" in line and "===" in line:
                skip_mode = 'warnings'
                content_removed = True
                continue

            # Detect start of coverage section
            if "---------- coverage:" in line:
                skip_mode = 'coverage'
                content_removed = True
                continue

            # Detect coverage LCOV line
            if "Coverage LCOV written" in line:
                content_removed = True
                continue

        # Check if we should stop skipping
        if skip_mode == 'session':
            # Session section ends at FAILURES, short test summary, or warnings summary
            if "===" in line and ("FAILURES" in line or "short test summary info" in line or "warnings summary" in line):
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Don't skip this line - it's a marker we want to keep (unless it's warnings)
                if "warnings summary" in line:
                    skip_mode = 'warnings'
                    content_removed = True
                    continue
            else:
                # Still in session section, skip this line
                continue

        elif skip_mode == 'warnings':
            # Warnings section ends at the Docs line or at FAILURES/short test summary
            if "-- Docs:" in line:
                skip_mode = None
                continue  # Skip the Docs line itself
            elif "===" in line and ("FAILURES" in line or "short test summary info" in line):
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Don't skip this line - it's a marker we want to keep
            else:
                # Still in warnings section, skip this line
                continue

        elif skip_mode == 'coverage':
            # Coverage section ends at blank line or at a marker line
            if line.strip() == "":
                skip_mode = None
                # Don't add the blank line yet, let normal processing handle it
                continue
            elif "===" in line:
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Don't skip this line - it's a marker we want to keep
            else:
                # Still in coverage section, skip this line
                continue

        # If we get here and skip_mode is None, add the line
        if skip_mode is None:
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

import re


def remove_pytest_sections(log: str | None) -> str | None:
    """
    Remove pytest test session and warnings sections from logs while keeping failures.

    This function removes:
    - Test session header and test results (from "test session starts" until FAILURES/summary)
    - Warnings summary section (can appear anywhere)
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

    def is_session_content_line(line: str) -> bool:
        """Check if a line is part of the test session content."""
        stripped = line.strip()
        if not stripped:
            return True  # Blank lines are part of session
        # Check for session info lines
        if any(keyword in line for keyword in ["platform ", "cachedir:", "rootdir:", "plugins:", "asyncio:", "collected ", "collecting "]):
            return True
        # Check for test result lines (end with [X%])
        if "[" in line and "%" in line and "]" in line:
            # Make sure it looks like a percentage (e.g., [  0%], [ 50%], [100%])
            if re.search(r'\[\s*\d+%\]', line):
                return True
        # Check for test result lines without percentage (e.g., "test_file.py .....F")
        # These lines typically have a file path followed by dots/status indicators
        if re.search(r'\.py\s+[\.FEsxXP]+\s*$', line):
            return True
        return False

    i = 0
    just_exited_skip_mode = False
    while i < len(lines):
        line = lines[i]

        # Check if we should start skipping
        if skip_mode is None:
            # Detect start of test session section
            if "test session starts" in line and "===" in line:
                skip_mode = 'session'
                content_removed = True
                i += 1
                continue

            # Detect start of warnings summary section
            if "warnings summary" in line and "===" in line:
                skip_mode = 'warnings'
                content_removed = True
                i += 1
                continue
            # Handle short test summary info marker
            if "===" in line and "short test summary info" in line:
                # Add blank line before summary if content was removed and last line is not blank
                if content_removed and filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                just_exited_skip_mode = False
                filtered_lines.append(line)
                i += 1
                continue
            # Handle FAILURES marker
            if just_exited_skip_mode and "===" in line and "FAILURES" in line:
                # Add blank line before FAILURES if content was removed and last line is not blank
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                filtered_lines.append(line)
                just_exited_skip_mode = False
                i += 1
                continue


            # Detect start of coverage section
            if "---------- coverage:" in line:
                skip_mode = 'coverage'
                content_removed = True
                i += 1
                continue

            # Detect coverage LCOV line (single line, not a section)
            if "Coverage LCOV written" in line:
                content_removed = True
                i += 1
                continue

            # If not skipping, add the line
            filtered_lines.append(line)
            just_exited_skip_mode = False
            i += 1
            continue

        # Handle skipping modes
        if skip_mode == 'session':
            # Check for explicit end markers
            if "===" in line and ("FAILURES" in line or "short test summary info" in line):
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Add this marker line
                filtered_lines.append(line)
                i += 1
                continue
            elif "===" in line and "warnings summary" in line:
                # Transition from session to warnings
                skip_mode = 'warnings'
                i += 1
                continue
            # Check if this line is part of session content
            elif is_session_content_line(line):
                # Still in session section, skip this line
                i += 1
                continue
            else:
                # This line is not part of session content, end session mode
                just_exited_skip_mode = True
                skip_mode = None
                # Don't add a blank line, just add this line
                filtered_lines.append(line)
                i += 1
                continue

        elif skip_mode == 'warnings':
            # Warnings section ends at the Docs line or at FAILURES/short test summary
            if "-- Docs:" in line:
                just_exited_skip_mode = True
                skip_mode = None
                i += 1
                continue  # Skip the Docs line itself
            elif "===" in line and ("FAILURES" in line or "short test summary info" in line):
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Add this marker line
                filtered_lines.append(line)
                i += 1
                continue
            else:
                # Still in warnings section, skip this line
                i += 1
                continue

        elif skip_mode == 'coverage':
            # Coverage section ends at blank line or at a marker line
            if line.strip() == "":
                skip_mode = None
                i += 1
                continue  # Skip the blank line after coverage
            elif "===" in line:
                skip_mode = None
                # Add blank line before the marker if needed
                if filtered_lines and filtered_lines[-1].strip():
                    filtered_lines.append("")
                # Add this marker line
                filtered_lines.append(line)
                i += 1
                continue
            else:
                # Still in coverage section, skip this line
                i += 1
                continue

        i += 1

    # Join the filtered lines
    result = "\n".join(filtered_lines)

    # If content was removed, reduce excessive blank lines (3+ consecutive) to 2
    if content_removed:
        result = re.sub(r'\n{3,}', '\n\n', result)

    return result

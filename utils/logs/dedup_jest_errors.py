import re

from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=lambda log: log, raise_on_error=False)
def dedup_jest_errors(log: str):
    """Deduplicate identical Jest test errors. When N tests fail with the same
    error, show the error once and list all N test names."""
    if not log:
        return log

    lines = log.split("\n")

    # Split into: preamble (before first FAIL), test file blocks, and footer (Test Suites/Tests summary)
    preamble: list[str] = []
    file_blocks: list[tuple[str, list[tuple[str, list[str]]]]] = []
    footer: list[str] = []

    current_file_header = ""
    current_test_name = ""
    current_error_body: list[str] = []
    current_tests: list[tuple[str, list[str]]] = []
    in_summary = False

    for line in lines:
        # Footer starts with "Test Suites:" or similar summary lines
        if re.match(
            r"^(Test Suites:|Tests:|Snapshots:|Time:|Ran all test suites)", line
        ):
            in_summary = True

        if in_summary:
            footer.append(line)
            continue

        # New file block
        if line.startswith("FAIL "):
            # Save previous file block
            if current_file_header:
                if current_test_name:
                    current_tests.append((current_test_name, current_error_body))
                file_blocks.append((current_file_header, current_tests))

            current_file_header = line
            current_tests = []
            current_test_name = ""
            current_error_body = []
            continue

        # New test error within a file block
        if re.match(r"^  ● ", line):
            if current_test_name:
                current_tests.append((current_test_name, current_error_body))
            current_test_name = line.strip()
            current_error_body = []
            continue

        # Content before any FAIL line
        if not current_file_header:
            preamble.append(line)
            continue

        # Error body lines
        if current_test_name:
            current_error_body.append(line)
        else:
            # Lines between FAIL header and first ● (shouldn't happen but handle gracefully)
            current_error_body.append(line)

    # Save last block
    if current_file_header:
        if current_test_name:
            current_tests.append((current_test_name, current_error_body))
        file_blocks.append((current_file_header, current_tests))

    # Now deduplicate within each file block
    result: list[str] = list(preamble)

    for file_header, tests in file_blocks:
        result.append(file_header)

        # Group tests by error signature (error message line, ignoring test-specific stack frames)
        groups: dict[str, list[tuple[str, list[str]]]] = {}
        group_order: list[str] = []
        for test_name, error_body in tests:
            # Extract error signature: first non-empty non-whitespace-only line of the body
            sig = ""
            for body_line in error_body:
                stripped = body_line.strip()
                if stripped:
                    sig = stripped
                    break
            if sig not in groups:
                groups[sig] = []
                group_order.append(sig)
            groups[sig].append((test_name, error_body))

        for sig in group_order:
            entries = groups[sig]
            if len(entries) == 1:
                # Single test - output normally
                test_name, error_body = entries[0]
                result.append(f"  {test_name}")
                result.extend(error_body)
                result.append("")
            else:
                # Multiple tests with same error - show error once, list test names
                first_name, first_body = entries[0]
                result.append(f"  {first_name}")
                result.extend(first_body)
                result.append("")
                result.append(f"  {len(entries)} tests failed with this same error:")
                for name, _body in entries:
                    result.append(f"    {name}")
                result.append("")

    result.extend(footer)
    return "\n".join(result)

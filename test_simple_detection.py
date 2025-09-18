from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the exact line from the failing case
test_line = "============================= test session starts =============================="
print(f"Test line: {repr(test_line)}")
print(f"Length: {len(test_line)}")
print(f"'===' in line: {'===' in test_line}")
print(f"'test session starts' in line: {'test session starts' in test_line}")
print(f"Both conditions: {'===' in test_line and 'test session starts' in test_line}")

# Test with minimal input
test_input = f"""Before
{test_line}
After"""

print(f"\nTest input: {repr(test_input)}")

# Manually trace through the logic
lines = test_input.split("\n")
skip = False
content_removed = False
filtered_lines = []

for i, line in enumerate(lines):
    print(f"\nProcessing line {i}: {repr(line)}")

    # Start skipping at test session header
    if "===" in line and "test session starts" in line:
        print(f"  -> MATCHED test session starts, setting skip=True")
        skip = True
        content_removed = True
        continue

    print(f"  -> skip={skip}")

    # Keep line if not skipping
    if not skip:
        print(f"  -> KEEPING line")
        filtered_lines.append(line)
    else:
        print(f"  -> SKIPPING line")
        content_removed = True

print(f"\nFiltered lines: {filtered_lines}")
manual_result = "\n".join(filtered_lines)
print(f"Manual result: {repr(manual_result)}")

# Now test with the actual function
actual_result = remove_pytest_sections(test_input)
print(f"Actual result: {repr(actual_result)}")
print(f"Results match: {manual_result == actual_result}")

# Test with a more complex case
complex_input = f"""Before
{test_line}
platform linux -- Python 3.12.11, pytest-8.3.3, pluggy-1.5.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2900 items
After"""

complex_result = remove_pytest_sections(complex_input)
print(f"\nComplex input: {repr(complex_input)}")
print(f"Complex result: {repr(complex_result)}")

expected_complex = """Before

After"""
print(f"Expected complex: {repr(expected_complex)}")
print(f"Complex matches expected: {complex_result == expected_complex}")

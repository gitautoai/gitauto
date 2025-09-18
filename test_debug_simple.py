from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the exact line from the failing case
test_line = "============================= test session starts =============================="
print(f"Test line: {repr(test_line)}")
print(f"'===' in line: {'===' in test_line}")
print(f"'test session starts' in line: {'test session starts' in test_line}")
print(f"Both conditions: {'===' in test_line and 'test session starts' in test_line}")

# Test with minimal case
test_input = """Before
============================= test session starts ==============================
Should be removed
After"""

result = remove_pytest_sections(test_input)
print(f"\nInput: {repr(test_input)}")
print(f"Result: {repr(result)}")

expected = """Before

After"""
print(f"Expected: {repr(expected)}")
print(f"Match: {result == expected}")

# Let's trace through the logic
print("\n" + "="*50)
print("TRACING LOGIC:")
lines = test_input.split("\n")
skip = False
content_removed = False
filtered_lines = []

for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")

    # Start skipping at test session header
    if "===" in line and "test session starts" in line:
        print(f"  -> MATCHED test session starts, setting skip=True")
        skip = True
        content_removed = True
        continue

    # Keep line if not skipping
    if not skip:
        print(f"  -> KEEPING line (skip={skip})")
        filtered_lines.append(line)
    else:
        print(f"  -> SKIPPING line (skip={skip})")
        content_removed = True

print(f"\nFiltered lines: {filtered_lines}")
result_manual = "\n".join(filtered_lines)
print(f"Manual result: {repr(result_manual)}")

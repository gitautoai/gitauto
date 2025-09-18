from utils.logs.remove_pytest_sections import remove_pytest_sections

# Minimal test case
test_input = """Line 1
============================= test session starts ==============================
Line 2
Line 3"""

result = remove_pytest_sections(test_input)
print(f"Input: {repr(test_input)}")
print(f"Result: {repr(result)}")

expected = """Line 1

"""
print(f"Expected: {repr(expected)}")
print(f"Match: {result == expected}")

# Test the line detection
lines = test_input.split("\n")
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")
    if "===" in line and "test session starts" in line:
        print(f"  -> MATCHES test session starts pattern")
    else:
        print(f"  -> Does not match test session starts pattern")

# Test with the exact line from the failing case
failing_line = "============================= test session starts =============================="
print(f"\nFailing line: {repr(failing_line)}")
print(f"'===' in line: {'===' in failing_line}")
print(f"'test session starts' in line: {'test session starts' in failing_line}")
print(f"Both: {'===' in failing_line and 'test session starts' in failing_line}")

# Test with that exact line
test_input2 = f"""Line 1
{failing_line}
Line 2
Line 3"""

result2 = remove_pytest_sections(test_input2)
print(f"\nInput2: {repr(test_input2)}")
print(f"Result2: {repr(result2)}")
expected2 = """Line 1

"""
print(f"Expected2: {repr(expected2)}")
print(f"Match2: {result2 == expected2}")

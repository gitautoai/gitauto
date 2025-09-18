from utils.logs.remove_pytest_sections import remove_pytest_sections

# Test the specific failing case
log = """Initial content
=========================== warnings summary ============================
/path/to/file.py:10: DeprecationWarning: deprecated function
  deprecated_function()

Final content"""

expected = """Initial content

Final content"""

result = remove_pytest_sections(log)
print("RESULT:")
print(repr(result))
print("\nEXPECTED:")
print(repr(expected))
print("\nMATCH:", result == expected)

if result != expected:
    print("\nDIFFERENCES:")
    result_lines = result.split('\n')
    expected_lines = expected.split('\n')
    max_len = max(len(result_lines), len(expected_lines))
    for i in range(max_len):
        r = result_lines[i] if i < len(result_lines) else "<MISSING>"
        e = expected_lines[i] if i < len(expected_lines) else "<MISSING>"
        if r != e:
            print(f"Line {i}: Got {repr(r)}, Expected {repr(e)}")
    print(f"Result length: {len(result_lines)}, Expected length: {len(expected_lines)}")

# Let's also test the logic step by step
print("\n" + "="*50)
print("STEP BY STEP DEBUG:")
lines = log.split("\n")
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")
    if line.strip() == "Final content":
        looks_like_regular_content = (
            not line.startswith(" ") and  # Not indented
            not line.startswith("/") and  # Not a file path
            "::" not in line and  # Not a test name
            "%" not in line and  # Not progress indicator
            "platform" not in line and "cachedir" not in line and "rootdir" not in line and
            "plugins" not in line and "collecting" not in line and "collected" not in line and
            "asyncio:" not in line and "=" not in line and
            " PASSED " not in line and " FAILED " not in line and " SKIPPED " not in line and " ERROR " not in line and
            not line.startswith("E ") and
            not (line.strip().startswith(".") and len(line.strip()) < 100)  # Not test progress dots
        )
        print(f"  -> looks_like_regular_content: {looks_like_regular_content}")
        print(f"  -> not line.startswith(' '): {not line.startswith(' ')}")
        print(f"  -> not line.startswith('/'): {not line.startswith('/')}")
        print(f"  -> '::' not in line: {'::' not in line}")
        print(f"  -> '%' not in line: {'%' not in line}")
        print(f"  -> '=' not in line: {'=' not in line}")

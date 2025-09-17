#!/usr/bin/env python3
import ast
import sys

# Check syntax of the remove_pytest_sections.py file
try:
    with open("utils/logs/remove_pytest_sections.py", "r") as f:
        source = f.read()

    # Try to parse the file
    ast.parse(source)
    print("✓ Syntax is valid")

except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    print(f"  Line {e.lineno}: {e.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Try to import the function
try:
    sys.path.insert(0, '.')
    from utils.logs.remove_pytest_sections import remove_pytest_sections
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import error: {e}")

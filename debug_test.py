#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.getcwd())

from utils.files.should_skip_ruby import should_skip_ruby
import re

# Debug the exact failing case
content = """API_BASE_URL = 'https://api.example.com'
API_VERSION = 'v1'
FULL_API_URL = "#{API_BASE_URL}/#{API_VERSION}"
CONFIG_HASH = {
  timeout: 30,
  retries: 3
}"""

print("Debugging line by line:")
lines = content.split("\n")
in_constant_definition = False
brace_count = 0

for i, line in enumerate(lines):
    stripped_line = line.strip()
    code_part = stripped_line.split('#')[0].strip()
    
    print(f"Line {i+1}: '{line}' -> stripped: '{stripped_line}' -> code: '{code_part}'")
    
    if not code_part:
        print("  -> Skipping (empty after removing comments)")
        continue
    
    if re.match(r"^[A-Z_][A-Z0-9_]*\s*=", code_part):
        print(f"  -> Matches constant pattern")
        brace_count = code_part.count("{") + code_part.count("[")
        brace_count -= code_part.count("}") + code_part.count("]")
        print(f"  -> Brace count: {brace_count}")
        if brace_count > 0:
            in_constant_definition = True
            print(f"  -> Starting multi-line constant definition")
    elif in_constant_definition:
        print(f"  -> Inside constant definition")
        brace_count += code_part.count("{") + code_part.count("[")
        brace_count -= code_part.count("}") + code_part.count("]")
        print(f"  -> Updated brace count: {brace_count}")
        if brace_count <= 0:
            in_constant_definition = False
            print(f"  -> Ending constant definition")
    else:
        print(f"  -> Other code found, should return False")
        break

result = should_skip_ruby(content)
print(f"\nFinal result: {result}")

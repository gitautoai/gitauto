#!/usr/bin/env python3

import sys
sys.path.append('/home/runner/work/gitauto/gitauto')

from utils.files.should_skip_rust import should_skip_rust

# Test the exact failing case
content = """struct Outer {
    inner: Inner,
}

enum Status {
    Active {
        timestamp: u64,
    },
    Inactive,
}

const CONSTANT: &str = "value";"""

result = should_skip_rust(content)
print(f"Result: {result}")
print(f"Expected: True")
print(f"Test {'PASSED' if result else 'FAILED'}")

if not result:
    print("ERROR: The fix did not work!")
    sys.exit(1)
else:
    print("SUCCESS: The fix works correctly!")
    sys.exit(0)

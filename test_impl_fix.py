#!/usr/bin/env python3
import sys
sys.path.append('.')
from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
content = """struct Config {}

impl Config {
    fn handler(&self) -> &str {
        "error"
    }

    fn process_data(&self, items: Vec<String>) -> Vec<String> {
        items
    }
}"""

result = should_skip_rust(content)
print(f"Result: {result}")
print(f"Expected: False")
print(f"Test passes: {result is False}")

if result is False:
    print("✅ Fix works correctly!")
else:
    print("❌ Fix did not work")

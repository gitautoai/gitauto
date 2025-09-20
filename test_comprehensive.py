#!/usr/bin/env python3
import sys
sys.path.append('.')
from utils.files.should_skip_rust import should_skip_rust

def test_case(name, content, expected):
    result = should_skip_rust(content)
    status = "✅" if result is expected else "❌"
    print(f"{status} {name}: {result} (expected {expected})")
    return result is expected

# Test cases
tests = [
    # Should return False (contains impl blocks)
    ("impl block", """struct Config {}

impl Config {
    fn handler(&self) -> &str {
        "error"
    }
}""", False),

    ("pub impl block", """struct Config {}

pub impl Config {
    fn new() -> Self {
        Config {}
    }
}""", False),

    # Should return True (only declarations)
    ("struct only", """struct Config {
    timeout: u32,
}

const CONSTANT: &str = "value";""", True),

    ("constants only", """const MAX_SIZE: i32 = 100;
const API_URL: &str = "https://api.com";""", True),

    ("use statements", """use std::collections::HashMap;
use serde::Serialize;
const CONSTANT: &str = "value";""", True),

    ("trait definition", """trait MyTrait {
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";""", True),
]

print("Testing impl block detection fix...")
print("=" * 50)

passed = 0
total = len(tests)

for name, content, expected in tests:
    if test_case(name, content, expected):
        passed += 1

print(f"\nResults: {passed}/{total} tests passed")

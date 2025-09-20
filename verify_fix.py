#!/usr/bin/env python3
"""
Quick verification script to test the impl block fix
"""
import sys
sys.path.append('.')
from utils.files.should_skip_rust import should_skip_rust

def test_case(name, content, expected):
    result = should_skip_rust(content)
    status = "✅" if result is expected else "❌"
    print(f"{status} {name}: {result} (expected {expected})")
    return result is expected

# Test the specific failing case
failing_test_content = """struct Config {}

impl Config {
    fn handler(&self) -> &str {
        "error"
    }

    fn process_data(&self, items: Vec<String>) -> Vec<String> {
        items
    }
}"""

print("Testing the specific failing case:")
print("=" * 50)
test_case("impl block (failing test)", failing_test_content, False)

print("\nTesting other key cases:")
print("=" * 30)

# Test other cases to make sure we didn't break anything
test_cases = [
    ("standalone fn", "fn main() { println!(\"Hello\"); }", False),
    ("pub fn", "pub fn helper() -> i32 { 42 }", False),
    ("macro_rules", "macro_rules! my_macro { () => { println!(\"test\"); }; }", False),
    ("struct only", "struct Config { timeout: u32, }", True),
    ("constants only", "const MAX_SIZE: i32 = 100;\nconst API_URL: &str = \"test\";", True),
    ("trait definition", "trait MyTrait { fn method(&self) -> String; }", True),
    ("use statements", "use std::collections::HashMap;\nconst VALUE: i32 = 42;", True),
]

passed = 1 if test_case("impl block (failing test)", failing_test_content, False) else 0
total = 1

for name, content, expected in test_cases:
    if test_case(name, content, expected):
        passed += 1
    total += 1

print(f"\nResults: {passed}/{total} tests passed")

if passed == total:
    print("🎉 All tests passed! The fix should work correctly.")
else:
    print("⚠️  Some tests failed. There might be an issue with the implementation.")

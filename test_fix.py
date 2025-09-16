#!/usr/bin/env python3

from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
content = """struct Config { value: String }
const CONFIG: Config = Config { value: env::var("VALUE").unwrap() };"""

result = should_skip_rust(content)
print(f"Result: {result}, Expected: False")
print("Test passed!" if result is False else "Test failed!")

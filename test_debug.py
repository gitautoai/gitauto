from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
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
print("Expected: True")
print(f"Test {'PASSED' if result else 'FAILED'}")

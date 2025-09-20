from utils.files.should_skip_rust import should_skip_rust

# Test the failing case
content = """pub struct Config
{
    timeout: u32,
}
const CONSTANT: &str = "value";"""

result = should_skip_rust(content)
print(f"Result: {result}")
print("Expected: True")

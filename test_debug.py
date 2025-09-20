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

# Test enum case
content2 = """pub enum Status
{
    Active,
    Inactive,
}
const CONSTANT: &str = "value";"""

result2 = should_skip_rust(content2)
print(f"Enum Result: {result2}")
print("Expected: True")

# Test trait case
content3 = """pub trait MyTrait
{
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";"""


from utils.files.should_skip_rust import should_skip_rust

def test_case(name, content, expected):
    result = should_skip_rust(content)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: {name} - Expected: {expected}, Got: {result}")
    return result == expected

# Test the original failing case
test_case("Nested struct/enum", """struct Outer {
    inner: Inner,
}

enum Status {
    Active {
        timestamp: u64,
    },
    Inactive,
}

const CONSTANT: &str = "value";""", True)

# Test simple struct
test_case("Simple struct", """pub struct Config {
    timeout: u32,
}
const CONSTANT: &str = "value";""", True)

# Test simple enum
test_case("Simple enum", """pub enum Status {
    Active,
    Inactive,
}
const CONSTANT: &str = "value";""", True)

# Test trait
test_case("Simple trait", """pub trait MyTrait {
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";""", True)

# Test struct without brace on same line
test_case("Struct separate brace", """pub struct Config
{
    timeout: u32,
}
const CONSTANT: &str = "value";""", True)

# Test enum without brace on same line
test_case("Enum separate brace", """pub enum Status
{
    Active,
    Inactive,
}
const CONSTANT: &str = "value";""", True)

# Test trait without brace on same line
test_case("Trait separate brace", """pub trait MyTrait
{
    fn method(&self) -> String;
}
const CONSTANT: &str = "value";""", True)

# Test with executable code (should return False)
test_case("With executable code", """const CONSTANT: &str = "value";
let variable = 42;  // This is executable code
const ANOTHER: &str = "value";""", False)

# Test deeply nested enum
test_case("Deeply nested enum", """enum Complex {
    Variant1 {
        field1: String,
        nested: NestedStruct {
            inner: i32,
        },
    },
    Variant2,
}
const CONSTANT: &str = "value";""", True)

print("\nTest completed!")

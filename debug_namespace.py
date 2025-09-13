from utils.files.should_skip_cpp import should_skip_cpp

content = """namespace utils {
    const int MAX_SIZE = 1000;
}

namespace config {
    const char* VERSION = "1.0.0";
}"""

print("Content:")
print(repr(content))
print("\nResult:", should_skip_cpp(content))

# Let's also test each line individually
lines = content.split('\n')
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line.strip())}")
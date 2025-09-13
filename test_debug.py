from utils.files.should_skip_cpp import should_skip_cpp

content = """enum Color {
    RED,
    GREEN,
    BLUE
};

enum class Status {
    PENDING,
    APPROVED,
    REJECTED
};"""

print(f"Result: {should_skip_cpp(content)}")
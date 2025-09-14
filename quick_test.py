import sys
sys.path.insert(0, '.')
from utils.files.should_skip_go import should_skip_go

# Test 1: Nested struct (should return True)
nested_struct = """package main

type Outer struct {
    Inner struct {
        Value string
        Count int
    }
    Name string
}"""

# Test 2: Simple struct (should return True)
simple_struct = """package main

type User struct {
    ID   int64
    Name string
}"""

# Test 3: Struct with method (should return False)
struct_with_method = """package main

type User struct {
    ID   int64
    Name string
}

func (u *User) GetName() string {
    return u.Name
}"""

# Test 4: Interface (should return True)
interface_only = """package main

type Reader interface {
    Read([]byte) (int, error)
}"""

tests = [
    ("Nested struct", nested_struct, True),
    ("Simple struct", simple_struct, True),
    ("Struct with method", struct_with_method, False),
    ("Interface only", interface_only, True),
]

all_passed = True
for name, content, expected in tests:
    result = should_skip_go(content)
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        all_passed = False
    print(f"{name}: {status} (got {result}, expected {expected})")

print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
import sys

sys.path.append('.')
from utils.files.should_skip_php import should_skip_php

# Test cases that should pass
test_cases = [
    # The failing test case
    {
        'name': 'test_opening_brace_detection',
        'content': """<?php
class MyClass
{
    public $property;
}""",
        'expected': True
    },
    # Interface with separate brace
    {
        'name': 'test_abstract_interface',
        'content': """<?php
abstract interface BaseInterface
{
    public function method(): string;
}""",
        'expected': True
    },
    # Trait with separate brace
    {
        'name': 'test_trait_without_opening_brace',
        'content': """<?php
trait MyTrait
{
}
const MAX_SIZE = 100;""",
        'expected': True
    },
    # Class with brace on same line (should still work)
    {
        'name': 'test_class_with_opening_brace_same_line',
        'content': """<?php
class MyClass {
    public $property;
}""",
        'expected': True
    },
    # Class with method (should NOT be skipped)
    {
        'name': 'test_class_with_method',
        'content': """<?php
class MyClass
{
    public function doSomething() {
        return true;
    }
}""",
        'expected': False
    }
]

for test in test_cases:
    result = should_skip_php(test['content'])
    print(f"{test['name']}: {result} (expected: {test['expected']}) - {'PASS' if result == test['expected'] else 'FAIL'}")

#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.coverages.parse_lcov_coverage import parse_lcov_coverage

def test_malformed_lines():
    """Test the exact case from the failing test"""
    lcov_content = """SF:src/malformed.py
FN:invalid_line
FNDA:not_a_number,func
BRDA:invalid_branch_data
DA:not_a_line,1
FN:10,20,30,too_many_parts
FNF:1
FNH:1
DA:10,1
LF:1
LH:1
end_of_record
"""
    
    print("Testing malformed lines...")
    try:
        result = parse_lcov_coverage(lcov_content)
        print(f"Malformed content result: {len(result)} reports")
        for i, report in enumerate(result):
            print(f"Report {i}: {report['level']} - {report['full_path']}")
        
        # Test the specific assertion from the failing test
        if len(result) == 3:
            print("✅ Test would PASS: len(result) == 3")
            return True
        else:
            print(f"❌ Test would FAIL: len(result) == {len(result)}, expected 3")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        print("Test would FAIL due to exception")
        return False

def test_empty_content():
    """Test empty content"""
    print("\nTesting empty content...")
    try:
        result = parse_lcov_coverage("")
        print(f"Empty content result: {len(result)} reports")
        if len(result) == 1:
            print("✅ Empty content test would PASS")
            return True
        else:
            print(f"❌ Empty content test would FAIL: expected 1, got {len(result)}")
            return False
    except Exception as e:
        print(f"❌ Exception occurred with empty content: {e}")
        return False

def test_basic_valid_content():
    """Test basic valid content"""
    print("\nTesting basic valid content...")
    lcov_content = """SF:src/example.py
FN:10,example_function
FNDA:1,example_function
FNF:1
FNH:1
DA:10,1
DA:11,1
DA:12,0
LF:3
LH:2
end_of_record
"""
    
    try:
        result = parse_lcov_coverage(lcov_content)
        print(f"Basic content result: {len(result)} reports")
        for i, report in enumerate(result):
            print(f"Report {i}: {report['level']} - {report['full_path']}")
        
        if len(result) == 3:
            print("✅ Basic content test would PASS")
            return True
        else:
            print(f"❌ Basic content test would FAIL: expected 3, got {len(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred with basic content: {e}")
        return False

# Run all tests
results = []
results.append(test_malformed_lines())
results.append(test_empty_content())
results.append(test_basic_valid_content())

print(f"\n=== SUMMARY ===")
print(f"Tests passed: {sum(results)}/{len(results)}")
if all(results):
    print("🎉 All tests would PASS!")
else:
    print("❌ Some tests would FAIL")
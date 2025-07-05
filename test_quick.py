#!/usr/bin/env python3
import sys
sys.path.append('.')

from services.coverages.parse_lcov_coverage import parse_lcov_coverage

def test_original_failing_case():
    """Test the exact case from the originally failing test"""
    print("=== TESTING ORIGINAL FAILING CASE ===")
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
    
    print("Input LCOV content:")
    print(lcov_content)
    print("Expected: 3 reports (file, directory, repository)")
    print("Processing...")
    
    try:
        result = parse_lcov_coverage(lcov_content)
        print(f"✅ SUCCESS: Got {len(result)} reports")
        
        for i, report in enumerate(result):
            print(f"  Report {i+1}: {report['level']} - '{report['full_path']}'")
        
        # Test the specific assertion from the failing test
        if len(result) == 3:
            print("✅ ASSERTION PASSES: len(result) == 3")
            
            # Check that we have the expected report types
            levels = [r['level'] for r in result]
            if 'file' in levels and 'directory' in levels and 'repository' in levels:
                print("✅ ASSERTION PASSES: All expected report types present")
                return True
            else:
                print(f"❌ ASSERTION FAILS: Missing report types. Got: {levels}")
                return False
        else:
            print(f"❌ ASSERTION FAILS: len(result) == {len(result)}, expected 3")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_error_cases():
    """Test various error cases to ensure robustness"""
    print("\n=== TESTING ALL ERROR CASES ===")
    
    test_cases = [
        ("FN with no comma", "SF:test.py\nFN:invalid_line\nend_of_record\n"),
        ("FN with too many parts", "SF:test.py\nFN:1,2,3,4,5\nend_of_record\n"),
        ("FNDA with invalid number", "SF:test.py\nFNDA:not_a_number,func\nend_of_record\n"),
        ("FNDA with no comma", "SF:test.py\nFNDA:invalid\nend_of_record\n"),
        ("BRDA with too few parts", "SF:test.py\nBRDA:invalid\nend_of_record\n"),
        ("BRDA with invalid numbers", "SF:test.py\nBRDA:a,b,c,d\nend_of_record\n"),
        ("DA with invalid line number", "SF:test.py\nDA:not_a_line,1\nend_of_record\n"),
        ("DA with no comma", "SF:test.py\nDA:invalid\nend_of_record\n"),
        ("FNF with invalid number", "SF:test.py\nFNF:not_a_number\nend_of_record\n"),
        ("FNH with invalid number", "SF:test.py\nFNH:not_a_number\nend_of_record\n"),
        ("BRF with invalid number", "SF:test.py\nBRF:not_a_number\nend_of_record\n"),
        ("BRH with invalid number", "SF:test.py\nBRH:not_a_number\nend_of_record\n"),
        ("LF with invalid number", "SF:test.py\nLF:not_a_number\nend_of_record\n"),
        ("LH with invalid number", "SF:test.py\nLH:not_a_number\nend_of_record\n"),
    ]
    
    all_passed = True
    for test_name, content in test_cases:
        print(f"\nTesting: {test_name}")
        try:
            result = parse_lcov_coverage(content)
            if len(result) == 3:  # Should always get file, directory, repository
                print(f"  ✅ PASS: {len(result)} reports")
            else:
                print(f"  ❌ FAIL: {len(result)} reports, expected 3")
                all_passed = False
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            all_passed = False
    
    return all_passed

def test_valid_cases():
    """Test that valid cases still work"""
    print("\n=== TESTING VALID CASES ===")
    
    test_cases = [
        ("Empty content", ""),
        ("Empty record", "SF:test.py\nend_of_record\n"),
        ("Basic valid", """SF:src/test.py
FN:10,func
FNDA:1,func
DA:10,1
end_of_record
"""),
        ("Complex valid", """SF:src/test.py
FN:10,20,func
FNDA:1,func
BRDA:15,1,jump to line 20,1
DA:10,1
DA:15,1
FNF:1
FNH:1
BRF:1
BRH:1
LF:2
LH:2
end_of_record
"""),
    ]
    
    all_passed = True
    for test_name, content in test_cases:
        print(f"\nTesting: {test_name}")
        try:
            result = parse_lcov_coverage(content)
            expected = 1 if test_name == "Empty content" else 3
            if len(result) == expected:
                print(f"  ✅ PASS: {len(result)} reports")
            else:
                print(f"  ❌ FAIL: {len(result)} reports, expected {expected}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            all_passed = False
    
    return all_passed

# Run all tests
print("🧪 COMPREHENSIVE TEST SUITE")
print("=" * 50)

results = []
results.append(test_original_failing_case())
results.append(test_all_error_cases())
results.append(test_valid_cases())

print(f"\n{'=' * 50}")
print(f"📊 FINAL RESULTS")
print(f"Tests passed: {sum(results)}/{len(results)}")

if all(results):
    print("🎉 ALL TESTS PASS! The fix should work!")
else:
    print("❌ Some tests failed. Need more investigation.")
    
print(f"{'=' * 50}")
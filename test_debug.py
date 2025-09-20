from utils.logs.remove_pytest_sections import remove_pytest_sections

log = """Before session
=========================== test session starts ============================
removed session content
Some important content between sections
=========================== warnings summary ============================
removed warnings content
More important content
=================================== FAILURES ===================================
failure content
Content after failures
=========================== short test summary info ============================
summary content
After summary"""

result = remove_pytest_sections(log)
print("RESULT:")
print(repr(result))
print("\nRESULT (formatted):")
print(result)

expected = """Before session

=================================== FAILURES ===================================
failure content
Content after failures

=========================== short test summary info ============================
summary content
After summary"""

print("\nEXPECTED:")
print(repr(expected))
print("\nMATCH:", result == expected)

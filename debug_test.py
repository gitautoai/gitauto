from utils.logs.remove_pytest_sections import remove_pytest_sections

log = """This line has === but no test session starts
This line has test session starts but no ===
This line has === and warnings but not warnings summary
This line has === and FAILED but not FAILURES
This line has === and short test but not summary info"""

result = remove_pytest_sections(log)
print("Original:")
print(repr(log))
print("Result:")
print(repr(result))
print("Equal:", result == log)

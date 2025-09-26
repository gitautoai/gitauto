import sys
sys.path.append('.')
from utils.logs.minimize_jest_test_logs import minimize_jest_test_logs

# Simplified version of the actual payload after ANSI codes are removed
input_log = """```CircleCI Build Log: yarn test
yarn run v1.22.22
$ craco test --watchAll=false --coverage=true --verbose=true
PASS test/utils/timeout.test.ts (10.698 s)
  timeout
    when timeout has not occurred
      ✓ should return false when start time equals current time (19 ms)

Summary of all failing tests
FAIL test/components/NewAccount/NewAccount.test.tsx (22.052 s)
  ● <NewAccount /> › Button Functionality › should copy URL to clipboard when copy button is clicked

    expect(jest.fn()).toHaveBeenCalledWith(...expected)

    Expected: "https://test-underwriting-url.com"

    Number of calls: 0

      614 |       await user.click(copyButton);
      615 |
    > 616 |       expect(mockWriteText).toHaveBeenCalledWith(testUrl);
          |                             ^
      617 |       expect(mockAlert).toHaveBeenCalledWith('Application URL copied to clipboard.');
      618 |     });
      619 |

      at Object.<anonymous> (test/components/NewAccount/NewAccount.test.tsx:616:29)

Test Suites: 1 failed, 36 passed, 37 total
Tests:       4 failed, 505 passed, 509 total
Snapshots:   0 total
Time:        37.513 s
Ran all test suites.
error Command failed with exit code 1.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.

Exited with code exit status 1

```"""

expected = """```CircleCI Build Log: yarn test
yarn run v1.22.22
$ craco test --watchAll=false --coverage=true --verbose=true

Summary of all failing tests
FAIL test/components/NewAccount/NewAccount.test.tsx (22.052 s)
  ● <NewAccount /> › Button Functionality › should copy URL to clipboard when copy button is clicked

    expect(jest.fn()).toHaveBeenCalledWith(...expected)

    Expected: "https://test-underwriting-url.com"

    Number of calls: 0

      614 |       await user.click(copyButton);
      615 |
    > 616 |       expect(mockWriteText).toHaveBeenCalledWith(testUrl);
          |                             ^
      617 |       expect(mockAlert).toHaveBeenCalledWith('Application URL copied to clipboard.');
      618 |     });
      619 |

      at Object.<anonymous> (test/components/NewAccount/NewAccount.test.tsx:616:29)

Test Suites: 1 failed, 36 passed, 37 total
Tests:       4 failed, 505 passed, 509 total
Snapshots:   0 total
Time:        37.513 s
Ran all test suites.
error Command failed with exit code 1.
info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command.

Exited with code exit status 1

```"""

result = minimize_jest_test_logs(input_log)
print("EXPECTED:")
print(repr(expected))
print("\nACTUAL:")
print(repr(result))
print("\nEXPECTED OUTPUT:")
print(expected)
print("\nACTUAL OUTPUT:")
print(result)
print("\nMATCH:", result == expected)

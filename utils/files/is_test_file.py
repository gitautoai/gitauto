import re, unicodedata
from utils.error.handle_exceptions import handle_exceptions


@handle_exceptions(default_return_value=False, raise_on_error=False)
def is_test_file(filename: str) -> bool:
    """
    Check if a file is a test file based on comprehensive patterns.
    Returns True if the file is a test file, False otherwise.
    """
    if not isinstance(filename, str):
        return False

    # Convert to lowercase for case-insensitive matching
    filename_lower = filename.lower()

    # Normalize unicode characters to their ASCII equivalents where possible
    # This helps with matching accented characters like 'é' -> 'e'
    try:
        filename_normalized = unicodedata.normalize('NFKD', filename_lower).encode('ASCII', 'ignore').decode('ASCII')
    except Exception:
        filename_normalized = filename_lower  # Fallback to lowercase if normalization fails

    # Test file naming patterns (more comprehensive than current)
    test_patterns = [
        # Direct test file patterns
        r"\.test\.",  # Button.test.tsx, utils.test.js
        r"\.spec\.",  # Button.spec.tsx, api.spec.js
        r"test\.",  # ButtonTest.java, UserTest.cs
        r"tests\.",  # ButtonTests.java, UserTests.cs
        r"_test\.",  # button_test.py, user_test.go
        r"_spec\.",  # button_spec.rb, user_spec.rb
        r"-test\.",  # file-test.py, component-test.js
        r"-spec\.",  # file-spec.rb, component-spec.js
        r"^test_",  # test_button.py, test_utils.py
        r"^test-",  # test-file.py, test-utils.py
        r"/test_",  # services/anthropic/test_client.py
        r"/test-",  # services/anthropic/test-client.py
        r"^spec_",  # spec_button.rb, spec_helper.rb
        r"^spec-",  # spec-button.rb, spec-helper.rb
        r"/spec_",  # services/anthropic/spec_client.py
        r"/spec-",  # services/anthropic/spec-client.py

        # Test directories
        r"/__tests__/",  # src/__tests__/Button.tsx
        r"/tests?/",  # src/tests/Button.tsx, src/test/Button.java
        r"^tests?/",  # tests/constants.py, test/utils.py
        r"(^|/)e2e/",  # e2e/login.spec.ts, src/e2e/login.spec.ts
        r"/test-",  # src/test-utils/component.js
        r"^test-",  # test-utils/component.js (already covered above but for clarity)
        r"(^|/)cypress/",  # cypress/integration/login.js, src/cypress/integration/login.js
        r"(^|/)playwright/",  # playwright/tests/login.spec.ts, src/playwright/tests/login.spec.ts
        r"/spec/",  # spec/models/user_spec.rb
        r"^spec/",  # spec/models/user_spec.rb (at beginning)
        r"(^|/)testing/",  # testing/utils.py, src/testing/utils.py

        # Mock files
        r"/__mocks__/",  # src/__mocks__/api.js
        r"\.mock\.",  # api.mock.ts, database.mock.js
        r"mock\.",  # ApiMock.java, DatabaseMock.cs
        r"mocks\.",  # ApiMocks.java, DatabaseMocks.cs

        # Common test file names
        r"^test\.",  # test.js, test.py
        r"^spec\.",  # spec.rb, spec.js

        # CI/CD and infrastructure
        r"^\.github/",  # .github/scripts/*, .github/workflows/*
    ]

    # Check against all patterns
    for pattern in test_patterns:
        if re.search(pattern, filename_lower) or re.search(pattern, filename_normalized):
            return True

    return False

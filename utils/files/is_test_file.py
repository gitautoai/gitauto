import re
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

    # Test file naming patterns (more comprehensive than current)
    test_patterns = [
        # Direct test file patterns
        r"\.test\.",  # Button.test.tsx, utils.test.js
        r"\.spec\.",  # Button.spec.tsx, api.spec.js
        r"test\.",  # ButtonTest.java, UserTest.cs
        r"tests\.",  # ButtonTests.java, UserTests.cs
        r"_test\.",  # button_test.py, user_test.go
        r"_spec\.",  # button_spec.rb, user_spec.rb
        r"^test_",  # test_button.py, test_utils.py
        r"/test_",  # services/anthropic/test_client.py
        r"^spec_",  # spec_button.rb, spec_helper.rb
        r"/spec_",  # services/anthropic/spec_client.py
        # Test directories
        r"/__tests__/",  # src/__tests__/Button.tsx
        r"/tests?/",  # src/tests/Button.tsx, src/test/Button.java
        r"^tests?/",  # tests/constants.py, test/utils.py
        r"/e2e/",  # e2e/login.spec.ts
        r"(^|/)cypress/",  # cypress/integration/login.js
        r"/playwright/",  # playwright/tests/login.spec.ts
        r"/spec/",  # spec/models/user_spec.rb
        r"/testing/",  # testing/utils.py
        # Mock files
        r"/__mocks__/",  # src/__mocks__/api.js
        r"\.mock\.",  # api.mock.ts, database.mock.js
        r"mock\.",  # ApiMock.java, DatabaseMock.cs
        r"mocks\.",  # ApiMocks.java, DatabaseMocks.cs
        # Snapshot files (Jest, Vitest, etc.)
        r"/__snapshots__/",  # __snapshots__/Button.test.tsx.snap
        r"\.snap$",  # any .snap file
        # Test fixtures and data
        r"(^|/)__fixtures__/",  # __fixtures__/user.json
        r"(^|/)fixtures/",  # fixtures/sample_data.json
        r"\.fixture\.",  # user.fixture.ts
        # Test configuration files
        r"jest\.config\.",  # jest.config.js, jest.config.ts
        r"vitest\.config\.",  # vitest.config.js
        r"karma\.conf\.",  # karma.conf.js
        r"\.spec\.snap$",  # component.spec.snap
        r"\.test\.snap$",  # component.test.snap
        # Test helpers and utilities
        r"(^|/)test[-_]utils?/",  # test-utils/, test_utils/
        r"(^|/)test[-_]helpers?/",  # test-helpers/, test_helper/
        r"(^|/)setuptests\.",  # setupTests.js, setupTests.ts
        r"(^|/)testsetup\.",  # testSetup.js, testSetup.ts
        r"^testsetup\.",  # testSetup.js at root
        r"(^|/)test[-_]setup\.",  # test-setup.js, test_setup.py
        # Storybook files (visual testing)
        r"\.stories\.",  # Button.stories.tsx
        r"(^|/)stories/",  # stories/Button.tsx
        # Common test file names
        r"^test\.",  # test.js, test.py
        r"^spec\.",  # spec.rb, spec.js
        # CI/CD and infrastructure
        r"^\.github/",  # .github/scripts/*, .github/workflows/*
    ]

    # Check against all patterns
    for pattern in test_patterns:
        if re.search(pattern, filename_lower):
            return True

    return False

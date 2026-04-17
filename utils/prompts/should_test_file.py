from utils.prompts.base_role import BASE_ROLE
from utils.quality_checks.checklist import QUALITY_CHECKLIST

SHOULD_TEST_FILE_PROMPT = f"""{BASE_ROLE} Look at this code and decide if it BOTH needs AND can be tested (solitary, sociable, and integration tests).

Return TRUE if the code is structurally testable (can be imported in a test without crashing) AND any of these apply:
1. The code has actual logic worth testing.
2. The code handles any of these quality concerns: {", ".join(QUALITY_CHECKLIST.keys())}.

For example, even simple code should be tested if it:
- Accepts user input (security: injection, XSS)
- Manages subscriptions/timers/listeners (memory: cleanup)
- Handles errors or shows messages to users (error_handling)
- Renders UI (accessibility, SEO)

Return FALSE if any of these apply:
- Standalone scripts that execute logic at the top level (not wrapped in functions/classes) and call exit/die/process.exit/sys.exit - these kill the test runner when loaded.
- PHP files that are entry-point scripts (not classes/functions) with top-level session_start(), header(), exit calls.
- Third-party code, generated files, examples, documentation, scripts, fixtures, etc.
- Do NOT reject files just because they import internal project dependencies, databases, or external services. These can be mocked in tests. Only reject files that would crash a test runner when imported (e.g. top-level process.exit, side effects on load).

Pay attention to the file path too - it can indicate the file should not be tested.

Keep the reason brief - one short sentence max."""

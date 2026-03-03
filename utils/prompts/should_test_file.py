SHOULD_TEST_FILE_PROMPT = """You are a very experienced senior engineer. Look at this code and decide if it BOTH needs AND can be unit tested.

Return TRUE only if BOTH conditions are met:
1. The code has actual logic worth testing.
2. The code is structurally testable - it can be imported/included in a test without crashing.

Return FALSE if any of these apply:
- Standalone scripts that execute logic at the top level (not wrapped in functions/classes) and call exit/die/process.exit/sys.exit - these kill the test runner when loaded.
- PHP files that are entry-point scripts (not classes/functions) with top-level session_start(), header(), exit calls.
- Third-party code, generated files, examples, documentation, scripts, fixtures, etc.
- Do NOT reject files just because they import internal project dependencies, databases, or external services. These can be mocked in tests. Only reject files that would crash a test runner when imported (e.g. top-level process.exit, side effects on load).

Pay attention to the file path too - it can indicate the file should not be tested.

Keep the reason brief - one short sentence max."""

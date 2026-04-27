# Each entry is { check_id: description }.
# The description is shown to the LLM evaluator so it can score concretely.
# The id stays as the stable key in stored results (no rename = no re-evaluation needed).
QUALITY_CHECKLIST: dict[str, dict[str, str]] = {
    "case_coverage": {
        "dimension_enumeration": "Every input dimension (parameter, flag, branch condition) is enumerated separately, not bundled into one happy-path test.",
        "combinatorial_matrix": "Combinations across multiple dimensions are exercised (not just one value per dimension), at least the meaningful ones.",
        "explicit_expected_per_cell": "Each parameterized case asserts a specific expected output for that input, not a generic shape check.",
    },
    "integration": {
        "db_operations_use_real_test_db": "Code that reads/writes a database is exercised against a real test DB (or in-memory equivalent), not a pure mock that only returns canned values.",
        "api_calls_tested_end_to_end": "Code that calls external APIs has at least one test against a real endpoint or recorded HTTP fixture, not only response-shape mocks.",
        "env_var_guards_for_secrets": "Integration tests requiring secrets/external services are guarded so they skip when env vars are absent (process.env.X / os.getenv / @pytest.mark.skipif / describe.skip), not unconditionally executed.",
    },
    "business_logic": {
        "domain_rules": "Domain-specific business rules (eligibility, pricing, validation policies) are explicitly asserted, not inferred from generic happy-path output.",
        "state_transitions": "Each state transition (allowed and forbidden) of stateful objects is exercised, including illegal transitions raising/erroring.",
        "calculation_accuracy": "Numeric calculations are verified with known-correct expected values (not just non-zero or type-checks); rounding and overflow edge cases are present.",
        "data_integrity": "Operations that mutate data preserve invariants (no orphan rows, FK consistency, no double-write, unique constraints respected).",
        "workflow_correctness": "Multi-step workflows assert the order and side effects of each step, not just the final output.",
    },
    "adversarial": {
        "null_undefined_inputs": "Each nullable parameter has a test passing null/undefined, asserting the documented behavior (default, error, or pass-through).",
        "empty_strings_arrays": "Empty string and empty collection inputs are tested (not just non-empty), with explicit expected behavior.",
        "boundary_values": "Boundary values are tested: 0, 1, max, max-1, negative when allowed; off-by-one regressions are catchable.",
        "type_coercion": "Type coercion edge cases (string '0' vs int 0, '1' vs true, numeric strings) are verified per the impl's stated contract.",
        "large_inputs": "Inputs larger than typical (10k+ items, multi-MB strings) are tested where impl claims to support them.",
        "race_conditions": "Concurrent or async invocations that may race share-state are explicitly tested (with controlled scheduling/promises), not just serial happy-path.",
        "unicode_special_chars": "Unicode (CJK, emoji, RTL), control chars, and special chars (quotes, backslashes, newlines) are tested where the impl handles strings.",
    },
    "security": {
        "xss": "User-controlled string output is asserted to be escaped/encoded; payloads like <script> are tested and shown not to execute or appear unescaped.",
        "sql_injection": "User-controlled values reaching SQL are asserted to be parameter-bound; payloads like ' OR 1=1 -- are tested and shown not to alter the query.",
        "command_injection": "User input reaching shell/exec is asserted to be quoted/escaped; payloads with ; && | $() are tested and shown not to execute.",
        "code_injection": "User input reaching eval/Function/dynamic-code paths is rejected or sandboxed; payloads attempting code execution are blocked.",
        "csrf": "State-changing endpoints are tested to require a valid CSRF token / origin / SameSite cookie; missing/forged tokens are rejected.",
        "auth_bypass": "Authorization checks are tested for: unauthenticated access, role escalation, IDOR (accessing another user's resource by id), expired tokens.",
        "sensitive_data_exposure": "Responses are tested not to leak passwords, tokens, PII, or stack traces in error paths.",
        "untrusted_input_sanitization": "Untrusted input crossing trust boundaries (HTML/SQL/Shell/file paths) is sanitized; both allow-list and deny-list paths are tested.",
        "open_redirects": "Redirect targets are validated against an allow-list; payloads with absolute external URLs and `//evil.com` are tested and rejected.",
        "path_traversal": "File path inputs are tested to reject `..`, absolute paths, and symlink escapes from the allowed root.",
    },
    "performance": {
        "quadratic_algorithms": "Code over collections is tested with growing input sizes to assert non-quadratic behavior (no nested-loop blowup, O(n) or better).",
        "heavy_sync_operations": "Sync I/O in hot paths is avoided or tested to be off the request path; tests assert async/streaming behavior where claimed.",
        "n_plus_1_queries": "Code that fetches related data is tested to issue a constant-bounded number of queries, not one per parent record.",
        "large_imports": "Modules in latency-sensitive paths are tested to avoid pulling in heavy transitive imports (or that's measured/justified).",
        "redundant_computation": "Code does not recompute expensive results within a single call; memoization or hoisting is verified via call counts on mocks.",
    },
    "memory": {
        "event_listener_cleanup": "Event listeners added in setup/effect are removed on teardown/cleanup; tests assert no listener leak across mount/unmount cycles.",
        "subscription_timer_cleanup": "Subscriptions, intervals, and timers started by the SUT are cancelled on teardown; tests assert no pending tasks remain.",
        "circular_references": "Long-lived data structures avoid retaining references that prevent GC; tests verify no growth under repeated invocation.",
        "closure_retention": "Long-lived closures don't capture large objects unnecessarily; tests show captured scope is minimized.",
    },
    "error_handling": {
        "graceful_degradation": "Failures of non-critical dependencies don't crash the SUT; tests assert fallback values/paths are exercised.",
        "user_error_messages": "User-facing error messages are explicit, actionable, and don't expose internal stack traces or paths; tested per error class.",
    },
    "accessibility": {
        "aria_attributes": "Interactive elements (buttons, dialogs, custom widgets) have correct ARIA roles/states; tests assert role and aria-* attributes.",
        "keyboard_navigation": "All interactive UI can be operated via keyboard alone (Tab/Shift+Tab/Enter/Space/Esc); tests fire key events and assert focus and action.",
        "screen_reader": "Dynamic regions announce updates (aria-live, role=status/alert); tests assert the announcement text is set on relevant updates.",
        "focus_management": "Focus is moved to opened dialogs/menus on open and restored on close; tests assert document.activeElement transitions.",
    },
    "seo": {
        "meta_tags": "Pages render correct <title>, <meta name=description>, og:*, and canonical tags; tests assert presence and exact values.",
        "semantic_html": "Pages use semantic landmarks (header/main/nav/article/aside/footer) rather than div soup; tests assert presence/structure.",
        "heading_hierarchy": "Heading levels are correct and not skipped (single h1, h2 under h1, etc.); tests assert the hierarchy.",
        "alt_text": "Every <img> has alt text (empty string for decorative, descriptive otherwise); tests assert alt presence and content.",
    },
}

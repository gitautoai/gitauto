"""
Test patterns for fix_missing_braces:

Each test case should follow these 3 patterns:

1. INLINE SIMPLIFIED - Small inline test case that demonstrates the issue
2. BROKEN TO CORRECT - Real fixture files testing detection and fix
3. CORRECT TO CORRECT - Real fixture files testing no false positives

RULES:
- For false positive tests (correct-to-correct): Pattern 3 alone is sufficient
- For detection tests (broken-to-correct): All 3 patterns are required
"""

from pathlib import Path

from utils.syntax.fix_missing_braces import fix_missing_braces

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# Basic: No missing braces
# =============================================================================


def test_no_missing_braces():
    content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    result = fix_missing_braces(content)
    assert not result["fixes"]
    assert result["content"] == content


# =============================================================================
# Missing test/it close
# =============================================================================


def test_detects_missing_test_close():
    broken = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  describe('other', () => {
    it('also works', () => {
    });
  });
});"""
    fixed = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });

  describe('other', () => {
    it('also works', () => {
    });
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 2,
            "block_type": "it",
            "insert_after_line": 3,
            "missing": "});",
        },
    ]
    assert result["content"] == fixed


# =============================================================================
# Missing describe close
# =============================================================================


def test_detects_missing_describe_close():
    broken = """describe('Error Handling', () => {
  test('throws error', () => {
    expect(() => {}).toThrow();
  });

describe('Component', () => {"""
    fixed = """describe('Error Handling', () => {
  test('throws error', () => {
    expect(() => {}).toThrow();
  });
});

describe('Component', () => {
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 1,
            "block_type": "describe",
            "insert_after_line": 4,
            "missing": "});",
        },
        {
            "block_start_line": 6,
            "block_type": "describe",
            "insert_after_line": 6,
            "missing": "});",
        },
    ]
    assert result["content"] == fixed


# =============================================================================
# Two missing in separate places
# =============================================================================


def test_detects_two_missing_separate_places():
    broken = """describe('suite', () => {
  it('test1', () => {
    expect(1).toBe(1);

  it('test2', () => {
    expect(2).toBe(2);
  });

  it('test3', () => {
    expect(3).toBe(3);

  it('test4', () => {
    expect(4).toBe(4);
  });
});"""
    fixed = """describe('suite', () => {
  it('test1', () => {
    expect(1).toBe(1);
  });

  it('test2', () => {
    expect(2).toBe(2);
  });

  it('test3', () => {
    expect(3).toBe(3);
  });

  it('test4', () => {
    expect(4).toBe(4);
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 2,
            "block_type": "it",
            "insert_after_line": 3,
            "missing": "});",
        },
        {
            "block_start_line": 9,
            "block_type": "it",
            "insert_after_line": 10,
            "missing": "});",
        },
    ]
    assert result["content"] == fixed


# =============================================================================
# Regular function syntax (not arrow functions)
# =============================================================================


def test_detects_missing_regular_function_close():
    broken = """describe('test', function() {
  it('works', function() {
    expect(true).toBe(true);

  it('also works', function() {
    expect(false).toBe(false);
  });
});"""
    fixed = """describe('test', function() {
  it('works', function() {
    expect(true).toBe(true);
  });

  it('also works', function() {
    expect(false).toBe(false);
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 2,
            "block_type": "it",
            "insert_after_line": 3,
            "missing": "});",
        },
    ]
    assert result["content"] == fixed


# =============================================================================
# waitFor missing close
# =============================================================================


def test_detects_missing_waitfor_close_inline():
    """Inline: waitFor missing close."""
    broken = """describe('Dashboard', () => {
  it('should load data', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.queryByTestId('loading-table')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Data loaded')).toBeInTheDocument();
    });
  });
});"""
    fixed = """describe('Dashboard', () => {
  it('should load data', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.queryByTestId('loading-table')).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Data loaded')).toBeInTheDocument();
    });
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 5,
            "block_type": "waitFor",
            "insert_after_line": 6,
            "missing": "});",
        },
    ]
    assert result["content"] == fixed


def test_detects_missing_waitfor_close_broken_to_correct():
    """Broken to correct: foxden-admin-portal PR #454 waitFor missing close."""
    broken = (
        FIXTURES_DIR
        / "broken_Foxquilt_foxden-admin-portal_pr454_waitfor_missing_close.test.tsx"
    ).read_text()
    correct = (
        FIXTURES_DIR
        / "correct_Foxquilt_foxden-admin-portal_pr454_waitfor_missing_close.test.tsx"
    ).read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 994,
            "block_type": "waitFor",
            "insert_after_line": 995,
            "missing": "});",
        },
    ]
    assert result["content"] == correct


def test_no_false_positives_waitfor_correct_to_correct():
    """Correct to correct: foxden-admin-portal PR #454 after fix."""
    content = (
        FIXTURES_DIR
        / "correct_Foxquilt_foxden-admin-portal_pr454_waitfor_missing_close.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# build_hooks missing close
# =============================================================================


def test_detects_build_hooks_missing():
    """Broken to correct: build_hooks missing one close."""
    broken = (FIXTURES_DIR / "broken_build_hooks.test.tsx").read_text()
    correct = (FIXTURES_DIR / "correct_build_hooks.test.tsx").read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 25,
            "block_type": "test",
            "insert_after_line": 56,
            "missing": "});",
        },
    ]
    assert result["content"] == correct


def test_detects_build_hooks_two_separate():
    """Broken to correct: build_hooks missing two closes in separate places."""
    broken = (FIXTURES_DIR / "broken_build_hooks_two_separate.test.tsx").read_text()
    correct = (FIXTURES_DIR / "correct_build_hooks.test.tsx").read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 6,
            "block_type": "test",
            "insert_after_line": 22,
            "missing": "});",
        },
        {
            "block_start_line": 58,
            "block_type": "test",
            "insert_after_line": 83,
            "missing": "});",
        },
    ]
    assert result["content"] == correct


def test_detects_build_hooks_two_in_row():
    """Broken to correct: build_hooks missing two closes in a row."""
    broken = (FIXTURES_DIR / "broken_build_hooks_two_in_row.test.tsx").read_text()
    correct = (FIXTURES_DIR / "correct_build_hooks.test.tsx").read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 5,
            "block_type": "describe",
            "insert_after_line": 84,
            "missing": "});",
        },
        {
            "block_start_line": 59,
            "block_type": "test",
            "insert_after_line": 84,
            "missing": "});",
        },
    ]
    assert result["content"] == correct


def test_detects_build_hooks_with_blank():
    """Broken to correct: build_hooks with blank lines."""
    broken = (FIXTURES_DIR / "broken_build_hooks_with_blank.test.tsx").read_text()
    correct = (FIXTURES_DIR / "correct_build_hooks.test.tsx").read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 6,
            "block_type": "test",
            "insert_after_line": 22,
            "missing": "});",
        },
        {
            "block_start_line": 58,
            "block_type": "test",
            "insert_after_line": 83,
            "missing": "});",
        },
    ]
    assert result["content"] == correct


def test_no_false_positives_build_hooks_correct_to_correct():
    """Correct to correct: build_hooks after fix."""
    content = (FIXTURES_DIR / "correct_build_hooks.test.tsx").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_reduxjs_build_hooks():
    """Correct to correct: real reduxjs buildHooks test file."""
    content = (FIXTURES_DIR / "correct_reduxjs_buildHooks.test.tsx").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# Nested missing braces
# =============================================================================


def test_detects_nested_missing_braces():
    """Broken to correct: nested describe/const missing braces."""
    broken = (FIXTURES_DIR / "missing_braces_nested.spec.ts").read_text()
    correct = (FIXTURES_DIR / "correct_nested.spec.ts").read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 475,
            "block_type": "describe",
            "insert_after_line": 512,
            "missing": "});",
        },
        {
            "block_start_line": 559,
            "block_type": "const",
            "insert_after_line": 568,
            "missing": "};",
        },
    ]
    assert result["content"] == correct


def test_no_false_positives_nested_correct_to_correct():
    """Correct to correct: nested after fix."""
    content = (FIXTURES_DIR / "correct_nested.spec.ts").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# Jest timeout pattern (}, 30000);
# =============================================================================


def test_no_false_positives_timeout_inline():
    """Inline: tests with timeout parameter should not trigger false positives."""
    content = """describe('Edge Cases', () => {
  it('handles null value', () => {
    const onChange = jest.fn();
    expect(onChange).toHaveBeenCalled();
  }, 30000);
});

describe('HTML Parsing', () => {
  it('parses HTML', () => {
    expect(true).toBe(true);
  });
});"""
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_timeout_correct_to_correct():
    """Correct to correct: foxcom-forms PR #1065 with Jest timeout pattern."""
    content = (
        FIXTURES_DIR / "correct_foxcom_forms_CoverageOption_timeout.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# Other real-world correct files (no false positives)
# =============================================================================


def test_no_false_positives_zod_to_json_schema():
    """Correct to correct: real zod to-json-schema test file."""
    content = (FIXTURES_DIR / "correct_zod_to-json-schema.test.ts").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_stripe_create_element_component():
    """Correct to correct: real stripe createElementComponent test file."""
    content = (
        FIXTURES_DIR / "correct_stripe_createElementComponent.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# mockReturnValue([ array argument missing close
# =============================================================================


def test_detects_missing_mockreturnvalue_array_close_inline():
    """Inline: mockReturnValue([ missing ]);"""
    broken = """describe('Test', () => {
  it('test case', async () => {
    mockFunction.mockReturnValue([
      mockArg,
      {
        data: undefined,
        loading: false
      } as any

    otherMockFunction.mockReturnValue([
      otherArg,
      { data: 'test' }
    ]);

    render(<Component />);
  });
});"""
    fixed = """describe('Test', () => {
  it('test case', async () => {
    mockFunction.mockReturnValue([
      mockArg,
      {
        data: undefined,
        loading: false
      } as any
    ]);

    otherMockFunction.mockReturnValue([
      otherArg,
      { data: 'test' }
    ]);

    render(<Component />);
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 3,
            "block_type": "mockReturnValue",
            "insert_after_line": 8,
            "missing": "]);",
        },
    ]
    assert result["content"] == fixed


def test_detects_missing_mockreturnvalue_array_close_broken_to_correct():
    """Broken to correct: foxcom-payment-frontend PR #508 mockReturnValue([ missing close and stray ]);."""
    broken = (
        FIXTURES_DIR
        / "broken_Foxquilt_foxcom-payment-frontend_pr508_mockReturnValue_array.test.tsx"
    ).read_text()
    correct = (
        FIXTURES_DIR
        / "correct_Foxquilt_foxcom-payment-frontend_pr508_mockReturnValue_array.test.tsx"
    ).read_text()
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "block_start_line": 965,
            "block_type": "mockReturnValue",
            "insert_after_line": 981,
            "missing": "]);",
        },
        {
            "removed_line": 997,
            "brace_type": "stray",
            "removed_content": "]);",
        },
    ]
    assert result["content"] == correct


def test_no_false_positives_mockreturnvalue_array_correct_to_correct():
    """Correct to correct: foxcom-payment-frontend PR #508 after fix."""
    content = (
        FIXTURES_DIR
        / "correct_Foxquilt_foxcom-payment-frontend_pr508_mockReturnValue_array.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


# =============================================================================
# Stray ]); (extra closing braces that should be removed)
# =============================================================================


def test_detects_stray_braces_inline():
    """Inline: stray ]); should be detected and removed."""
    broken = """describe('Test', () => {
  it('test case', async () => {
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
    ]);
  });
});"""
    fixed = """describe('Test', () => {
  it('test case', async () => {
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });
});"""
    result = fix_missing_braces(broken)
    assert result["fixes"] == [
        {
            "removed_line": 6,
            "brace_type": "stray",
            "removed_content": "]);",
        },
    ]
    assert result["content"] == fixed


def test_no_false_positives_stray_braces_inline():
    """Inline: valid ]); patterns should not be removed."""
    content = """describe('Test', () => {
  it('test case', async () => {
    mockFunction.mockReturnValue([
      mockArg,
      { data: 'test' }
    ]);

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });
});"""
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_stray_braces_correct_to_correct():
    """Correct to correct: files with valid ]); should not be modified."""
    content = (
        FIXTURES_DIR
        / "correct_Foxquilt_foxcom-payment-frontend_pr508_mockReturnValue_array.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content

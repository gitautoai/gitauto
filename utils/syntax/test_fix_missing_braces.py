from pathlib import Path

from utils.syntax.fix_missing_braces import fix_missing_braces

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_no_missing_braces():
    content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    result = fix_missing_braces(content)
    assert not result["fixes"]
    assert result["content"] == content


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


def test_detects_build_hooks_missing():
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


def test_detects_nested_missing_braces():
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


def test_detects_missing_waitfor_close():
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


def test_real_broken_foxquilt_pr454_waitfor_missing_close():
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


def test_no_false_positives_reduxjs_build_hooks():
    content = (FIXTURES_DIR / "correct_reduxjs_buildHooks.test.tsx").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_zod_to_json_schema():
    content = (FIXTURES_DIR / "correct_zod_to-json-schema.test.ts").read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_stripe_create_element_component():
    content = (
        FIXTURES_DIR / "correct_stripe_createElementComponent.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content


def test_no_false_positives_test_with_timeout():
    """Tests with timeout parameter like `}, 30000);` should not trigger false positives."""
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


def test_no_false_positives_foxcom_forms_coverage_option_timeout():
    """Real file from foxcom-forms PR #1065 with Jest timeout pattern."""
    content = (
        FIXTURES_DIR / "correct_foxcom_forms_CoverageOption_timeout.test.tsx"
    ).read_text()
    result = fix_missing_braces(content)
    assert result["fixes"] == []
    assert result["content"] == content

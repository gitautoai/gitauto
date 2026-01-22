from pathlib import Path

from utils.syntax.detect_missing_braces import detect_missing_braces

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_no_missing_braces():
    content = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);
  });
});"""
    result = detect_missing_braces(content)
    assert not result


def test_detects_missing_test_close():
    # Missing: }); after line 3
    broken = """describe('test', () => {
  it('works', () => {
    expect(true).toBe(true);

  describe('other', () => {
    it('also works', () => {
    });
  });
});"""
    result = detect_missing_braces(broken)
    assert result == [
        {
            "block_start_line": 2,
            "block_type": "it",
            "insert_after_line": 3,
            "missing": "});",
        },
    ]


def test_detects_missing_describe_close():
    # Missing: }); after line 4
    broken = """describe('Error Handling', () => {
  test('throws error', () => {
    expect(() => {}).toThrow();
  });

describe('Component', () => {"""
    result = detect_missing_braces(broken)
    assert result == [
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


def test_detects_two_missing_separate_places():
    # Missing: }); after line 3 and after line 9
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
    result = detect_missing_braces(broken)
    assert result == [
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


def test_detects_build_hooks_missing():
    # Missing: }); after second test (line 57)
    broken = (FIXTURES_DIR / "broken_build_hooks.test.tsx").read_text()
    result = detect_missing_braces(broken)
    assert result == [
        {
            "block_start_line": 25,
            "block_type": "test",
            "insert_after_line": 56,
            "missing": "});",
        },
    ]


def test_detects_build_hooks_two_separate():
    # Missing: }); after first test (line 23) and after third test (line 84)
    broken = (FIXTURES_DIR / "broken_build_hooks_two_separate.test.tsx").read_text()
    result = detect_missing_braces(broken)
    assert result == [
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


def test_detects_build_hooks_two_in_row():
    # Missing: }); after third test and }); after describe (both insert at line 85)
    broken = (FIXTURES_DIR / "broken_build_hooks_two_in_row.test.tsx").read_text()
    result = detect_missing_braces(broken)
    assert result == [
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


def test_detects_build_hooks_with_blank():
    # Missing: }); after first test (line 23) and after third test (line 84), with blank lines
    broken = (FIXTURES_DIR / "broken_build_hooks_with_blank.test.tsx").read_text()
    result = detect_missing_braces(broken)
    assert result == [
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

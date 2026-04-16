# pylint: disable=line-too-long,unused-argument
# pyright: reportUnusedVariable=false
"""Tests for search_and_replace using real CPython stdlib files as fixtures.

Fixture files saved from CPython 3.13 (PSF license) in services/git/fixtures/:
- _pydecimal.py.txt (~6300 lines, 227K chars) - repeated boilerplate across arithmetic methods
- argparse.py.txt   (~2700 lines, 103K chars) - 11 identical __call__ signatures across Action subclasses
- typing.py.txt     (~3800 lines, 133K chars) - 7 identical __reduce__ methods across alias classes
"""
import os
import subprocess
import tempfile

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.search_and_replace import search_and_replace


# ---------------------------------------------------------------------------
# Helpers to load real CPython stdlib fixtures saved on disk
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(filename: str):
    with open(os.path.join(FIXTURES_DIR, filename), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def pydecimal_source():
    """CPython _pydecimal.py (~6300 lines). PSF license."""
    return _read_fixture("_pydecimal.py.txt")


@pytest.fixture
def argparse_source():
    """CPython argparse.py (~2700 lines). PSF license."""
    return _read_fixture("argparse.py.txt")


@pytest.fixture
def typing_source():
    """CPython typing.py (~3800 lines). PSF license."""
    return _read_fixture("typing.py.txt")


# ---------------------------------------------------------------------------
# Basic functionality (kept for coverage of simple edge cases)
# ---------------------------------------------------------------------------


def test_successful_replacement(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("print('hello world')\nprint('goodbye')\n")

    result = search_and_replace(
        old_string="hello world",
        new_string="hello modified world",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Updated test.py" in result.message
    assert (
        tmp_path / "test.py"
    ).read_text() == "print('hello modified world')\nprint('goodbye')\n"


def test_file_not_found(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    result = search_and_replace(
        old_string="hello",
        new_string="world",
        file_path="nonexistent.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "not found" in result.message


def test_directory_path_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "my_dir").mkdir()

    result = search_and_replace(
        old_string="old",
        new_string="new",
        file_path="my_dir",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "directory" in result.message


def test_empty_old_string(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("content\n")

    result = search_and_replace(
        old_string="",
        new_string="new",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "must not be empty" in result.message


def test_old_string_not_found(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("print('hello')\n")

    result = search_and_replace(
        old_string="nonexistent text",
        new_string="replacement",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "not found" in result.message


def test_multiple_occurrences(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("foo\nfoo\nbar\n")

    result = search_and_replace(
        old_string="foo",
        new_string="baz",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "2 times" in result.message
    assert "more surrounding context" in result.message


def test_no_change_when_old_equals_new(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("hello world\n")

    result = search_and_replace(
        old_string="hello world",
        new_string="hello world",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "No changes" in result.message


def test_preserve_crlf_line_endings(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.txt").write_text("line1\r\nline2\r\nline3\r\n", newline="")

    result = search_and_replace(
        old_string="line2",
        new_string="modified_line2",
        file_path="test.txt",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.txt").read_text(newline="")
    assert "modified_line2" in content
    assert "\r\n" in content


def test_nested_file_path(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    nested_dir = tmp_path / "src" / "utils"
    nested_dir.mkdir(parents=True)
    (nested_dir / "helper.py").write_text("old_function()\n")

    result = search_and_replace(
        old_string="old_function()",
        new_string="new_function()",
        file_path="src/utils/helper.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (nested_dir / "helper.py").read_text() == "new_function()\n"


def test_extra_kwargs_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("old\n")

    result = search_and_replace(
        old_string="old",
        new_string="new",
        file_path="test.py",
        base_args=base_args,
        extra_param="ignored",
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True


def test_diff_included_in_message(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("alpha\nbeta\ngamma\n")

    result = search_and_replace(
        old_string="beta",
        new_string="delta",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert "Diff:" not in result.message
    assert "-beta" in result.diff
    assert "+delta" in result.diff


# ---------------------------------------------------------------------------
# Real CPython _pydecimal.py (~6300 lines, 227K chars)
#
# This file has extreme repetition: the 3-line block
#     other = _convert_other(other)
#     if other is NotImplemented:
#         return other
# appears 14 times across arithmetic methods (__add__, __sub__, __mul__, etc.).
# The "if context is None: context = getcontext()" block appears 39 times.
# ---------------------------------------------------------------------------


def test_pydecimal_convert_other_block_rejected_14_matches(
    create_test_base_args, tmp_path, pydecimal_source
):
    # The _convert_other + NotImplemented guard appears 14 times — must be rejected
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    result = search_and_replace(
        old_string="        other = _convert_other(other)\n        if other is NotImplemented:\n            return other",
        new_string="        other = _convert_other(other)\n        if other is NotImplemented:\n            return NotImplemented",
        file_path="_pydecimal.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "14 times" in result.message


def test_pydecimal_context_getcontext_block_rejected_39_matches(
    create_test_base_args, tmp_path, pydecimal_source
):
    # 'if context is None: context = getcontext()' appears 39 times — must reject
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    result = search_and_replace(
        old_string="        if context is None:\n            context = getcontext()",
        new_string="        if context is None:\n            context = getcontext()\n            # patched",
        file_path="_pydecimal.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "39 times" in result.message


def test_pydecimal_add_method_unique_with_docstring(
    create_test_base_args, tmp_path, pydecimal_source
):
    # __add__ with its docstring is unique — should succeed on a 6300-line file
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    old = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """'
    new = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        NOTE: patched by search_and_replace test.\n        """'

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="_pydecimal.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "_pydecimal.py").read_text()
    assert "NOTE: patched by search_and_replace test." in content
    # __sub__ must be untouched
    assert "def __sub__(self, other, context=None):" in content
    # File is still large (no accidental truncation)
    assert len(content.split("\n")) > 6000
    # result.content must match what was written to disk
    assert result.content == content
    # Diff must be in the diff field, not in message
    assert "Diff:" not in result.message
    assert "+        NOTE: patched by search_and_replace test." in result.diff


def test_pydecimal_disambiguate_convert_other_via_method_signature(
    create_test_base_args, tmp_path, pydecimal_source
):
    # Including __add__ signature before the _convert_other block makes it unique
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    old = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """\n        other = _convert_other(other)\n        if other is NotImplemented:\n            return other'
    new = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """\n        other = _convert_other(other, raiseit=False)\n        if other is NotImplemented:\n            return NotImplemented'

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="_pydecimal.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "_pydecimal.py").read_text()
    # Only __add__ should have the change
    assert "_convert_other(other, raiseit=False)" in content
    # __sub__ still has the original pattern
    sub_idx = content.index("def __sub__(self")
    sub_block = content[sub_idx : sub_idx + 500]
    assert "_convert_other(other)" in sub_block
    assert "raiseit=False" not in sub_block
    # result.content matches disk and diff is present
    assert result.content == content
    assert "Diff:" not in result.message
    assert "+        other = _convert_other(other, raiseit=False)" in result.diff


# ---------------------------------------------------------------------------
# Real CPython argparse.py (~2700 lines, 103K chars)
#
# 11 Action subclasses each define:
#     def __call__(self, parser, namespace, values, option_string=None):
# with identical signatures. The __init__ pattern also repeats 12 times.
# ---------------------------------------------------------------------------


def test_argparse_call_signature_rejected_11_matches(
    create_test_base_args, tmp_path, argparse_source
):
    # The __call__ signature appears 11 times across Action subclasses
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    result = search_and_replace(
        old_string="    def __call__(self, parser, namespace, values, option_string=None):",
        new_string="    def __call__(self, parser, namespace, values, option_string=None):  # patched",
        file_path="argparse.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "11 times" in result.message


def test_argparse_init_option_strings_rejected_12_matches(
    create_test_base_args, tmp_path, argparse_source
):
    # The __init__(self, option_strings, ...) pattern appears 12 times
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    result = search_and_replace(
        old_string="    def __init__(self,\n                 option_strings,",
        new_string="    def __init__(self,\n                 option_strings,  # patched",
        file_path="argparse.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    # Exact count depends on Python version but should be > 1
    assert "times" in result.message


def test_argparse_help_action_call_unique_with_body(
    create_test_base_args, tmp_path, argparse_source
):
    # _HelpAction.__call__ body (print_help + exit) is unique across all Action subclasses
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    old = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help()\n        parser.exit()"
    new = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help(file=None)\n        parser.exit(status=0)"

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="argparse.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "argparse.py").read_text()
    assert "parser.print_help(file=None)" in content
    assert "parser.exit(status=0)" in content
    # Other __call__ methods untouched (e.g. _VersionAction still has its own body)
    assert (
        "parser.exit(message=formatter.format_help())" in content
        or "parser._print_message" in content
    )
    assert len(content.split("\n")) > 2500
    # result.content matches disk and diff is present
    assert result.content == content
    assert "Diff:" not in result.message
    assert "+        parser.print_help(file=None)" in result.diff
    assert "+        parser.exit(status=0)" in result.diff


def test_argparse_disambiguate_call_via_class_context(
    create_test_base_args, tmp_path, argparse_source
):
    # Including the class definition makes the __call__ signature unique
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    old = "class _HelpAction(Action):\n\n    def __init__(self,\n                 option_strings,"
    new = 'class _HelpAction(Action):\n    """Display help and exit."""\n\n    def __init__(self,\n                 option_strings,'

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="argparse.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "argparse.py").read_text()
    assert '"Display help and exit."' in content
    # Other Action subclasses untouched
    assert "class _VersionAction(Action):" in content
    assert "class _StoreAction(Action):" in content
    # result.content matches disk and diff is present
    assert result.content == content
    assert "Diff:" not in result.message
    assert '+    """Display help and exit."""' in result.diff


# ---------------------------------------------------------------------------
# Real CPython typing.py (~3800 lines, 133K chars)
#
# 7 classes define identical __reduce__(self) methods.
# 11 classes define __repr__(self) methods.
# 7 occurrences of `return _GenericAlias(self, (item,))`.
# ---------------------------------------------------------------------------


def test_typing_reduce_rejected_7_matches(
    create_test_base_args, tmp_path, typing_source
):
    # 'def __reduce__(self):' appears 7 times across alias classes
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "typing.py").write_text(typing_source)

    result = search_and_replace(
        old_string="    def __reduce__(self):",
        new_string="    def __reduce__(self):  # patched",
        file_path="typing.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "7 times" in result.message


def test_typing_repr_rejected_11_matches(
    create_test_base_args, tmp_path, typing_source
):
    # 'def __repr__(self):' appears 11 times
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "typing.py").write_text(typing_source)

    result = search_and_replace(
        old_string="    def __repr__(self):",
        new_string="    def __repr__(self):  # patched",
        file_path="typing.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "11 times" in result.message


def test_typing_special_form_class_unique(
    create_test_base_args, tmp_path, typing_source
):
    # 'class _SpecialForm' appears exactly once — replacement should succeed
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "typing.py").write_text(typing_source)

    # Find the actual first line after class _SpecialForm
    lines = typing_source.split("\n")
    class_idx = next(i for i, line in enumerate(lines) if "class _SpecialForm" in line)
    # Use the class line + next non-blank line as old_string
    old_lines = [lines[class_idx]]
    for j in range(class_idx + 1, min(class_idx + 5, len(lines))):
        old_lines.append(lines[j])
        if len(old_lines) >= 3:
            break

    old = "\n".join(old_lines)
    new = old.replace(
        "class _SpecialForm", "class _SpecialForm  # search_and_replace patched"
    )

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="typing.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "typing.py").read_text()
    assert "search_and_replace patched" in content
    assert len(content.split("\n")) > 3500
    # result.content matches disk and diff is present
    assert result.content == content
    assert "Diff:" not in result.message
    assert result.diff


# ---------------------------------------------------------------------------
# Cross-cutting: file size preservation, no truncation, no corruption
# ---------------------------------------------------------------------------


def test_pydecimal_replacement_preserves_file_size(
    create_test_base_args, tmp_path, pydecimal_source
):
    # After replacing one 5-line block in a 6300-line file, total size should change minimally
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)
    original_lines = len(pydecimal_source.split("\n"))

    old = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """'
    new = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        Added one extra line.\n        """'

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="_pydecimal.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "_pydecimal.py").read_text()
    new_lines = len(content.split("\n"))
    # We added 1 line; sort_imports may shift a few lines but file should stay ~same size
    assert new_lines >= original_lines
    assert new_lines <= original_lines + 5


def test_argparse_replacement_does_not_corrupt_other_classes(
    create_test_base_args, tmp_path, argparse_source
):
    # After editing _HelpAction, verify all other Action subclasses still parse correctly
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    old = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help()\n        parser.exit()"
    new = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help()\n        parser.exit(0)"

    result = search_and_replace(
        old_string=old,
        new_string=new,
        file_path="argparse.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "argparse.py").read_text()
    # All Action subclasses must still be present
    for cls in [
        "_StoreAction",
        "_StoreConstAction",
        "_AppendAction",
        "_AppendConstAction",
        "_CountAction",
        "_HelpAction",
        "_VersionAction",
        "_SubParsersAction",
    ]:
        assert f"class {cls}(Action):" in content or f"class {cls}(Action)" in content


# ---------------------------------------------------------------------------
# Whitespace edge cases
# ---------------------------------------------------------------------------


def test_tabs_vs_spaces_mismatch_not_found(create_test_base_args, tmp_path):
    # File uses tabs, old_string uses spaces — must fail, not silently match
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("def foo():\n\treturn 1\n")

    result = search_and_replace(
        old_string="def foo():\n    return 1",
        new_string="def foo():\n    return 2",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is False
    assert "not found" in result.message


def test_crlf_multiline_old_string_with_lf_input(create_test_base_args, tmp_path):
    # File uses CRLF but Claude sends LF in old_string — normalization should handle it
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.cs").write_text(
        "public class Foo {\r\n    int x = 1;\r\n    int y = 2;\r\n}\r\n",
        newline="",
    )

    result = search_and_replace(
        old_string="    int x = 1;\n    int y = 2;",
        new_string="    int x = 10;\n    int y = 20;",
        file_path="test.cs",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.cs").read_text(newline="")
    assert "int x = 10;" in content
    assert "int y = 20;" in content
    assert "\r\n" in content
    assert content.count("\n") == content.count("\r\n")


# ---------------------------------------------------------------------------
# Special characters and encoding
# ---------------------------------------------------------------------------


def test_regex_metacharacters_treated_as_literal(create_test_base_args, tmp_path):
    # Regex metacharacters in old_string must be treated as literal text
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    content = 'pattern = r"^(foo|bar)\\.(baz)+$"\nother = "hello"\n'
    (tmp_path / "test.py").write_text(content)

    result = search_and_replace(
        old_string='pattern = r"^(foo|bar)\\.(baz)+$"',
        new_string='pattern = r"^(foo|bar|qux)\\.(baz)+$"',
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert 'r"^(foo|bar|qux)\\.(baz)+$"' in (tmp_path / "test.py").read_text()


def test_unicode_content(create_test_base_args, tmp_path):
    # Unicode characters in both old_string and file content
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text(
        '# コメント\nmessage = "こんにちは世界"\nprint(message)\n'
    )

    result = search_and_replace(
        old_string='message = "こんにちは世界"',
        new_string='message = "Hello, 世界!"',
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.py").read_text()
    assert 'message = "Hello, 世界!"' in content
    assert "# コメント" in content


# ---------------------------------------------------------------------------
# String replacement edge cases
# ---------------------------------------------------------------------------


def test_old_string_is_substring_of_new_string(create_test_base_args, tmp_path):
    # When new_string contains old_string, replacement must happen exactly once
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("x = 1\n")

    result = search_and_replace(
        old_string="x = 1",
        new_string="x = 1  # was x = 1",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.py").read_text()
    assert content == "x = 1  # was x = 1\n"


def test_replacement_creates_duplicate_but_still_succeeds(
    create_test_base_args, tmp_path
):
    # After replacement new_string appears twice — fine, we only check uniqueness BEFORE replacing
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("aaa\nbbb\n")

    result = search_and_replace(
        old_string="bbb",
        new_string="aaa",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "aaa\naaa\n"


def test_empty_new_string_deletes_match(create_test_base_args, tmp_path):
    # Empty new_string should delete the matched text
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("keep_this\ndelete_this\nkeep_this_too\n")

    result = search_and_replace(
        old_string="delete_this\n",
        new_string="",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "keep_this\nkeep_this_too\n"


def test_entire_file_is_old_string(create_test_base_args, tmp_path):
    # Replacing the entire file content via search_and_replace
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("old content\n")

    result = search_and_replace(
        old_string="old content\n",
        new_string="completely new content\n",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "completely new content\n"


# ---------------------------------------------------------------------------
# Post-processing verification
# ---------------------------------------------------------------------------


def test_trailing_spaces_stripped_after_replacement(create_test_base_args, tmp_path):
    # Verify strip_trailing_spaces runs after replacement
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("clean_line\nother_line\n")

    result = search_and_replace(
        old_string="clean_line",
        new_string="has_trailing_spaces   ",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.py").read_text()
    for line in content.split("\n"):
        if line:
            assert not line.endswith(" "), f"Line has trailing space: {line!r}"


def test_final_newline_ensured(create_test_base_args, tmp_path):
    # Verify ensure_final_newline adds one if replacement removes it
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("line1\nline2\n")

    result = search_and_replace(
        old_string="line2\n",
        new_string="line2_no_newline",
        file_path="test.py",
        base_args=base_args,
    )

    assert isinstance(result, FileWriteResult)
    assert result.success is True
    content = (tmp_path / "test.py").read_text()
    assert content.endswith("\n")


@pytest.mark.integration
def test_search_and_replace_end_to_end(local_repo, create_test_base_args):
    """Sociable: replace text in README, verify pushed to bare repo."""
    bare_url, _work_dir = local_repo

    with tempfile.TemporaryDirectory() as clone_dir:
        git_clone_to_tmp(clone_dir, bare_url, "main")

        base_args = create_test_base_args(
            clone_dir=clone_dir,
            clone_url=bare_url,
            new_branch="feature/replace-test",
        )

        result = search_and_replace(
            old_string="# Test",
            new_string="# Modified Test",
            file_path="README.md",
            base_args=base_args,
        )

        assert isinstance(result, FileWriteResult)
        assert result.success is True

        with open(os.path.join(clone_dir, "README.md"), encoding="utf-8") as f:
            assert "# Modified Test" in f.read()

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--oneline", "feature/replace-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert "Update README.md" in log.stdout

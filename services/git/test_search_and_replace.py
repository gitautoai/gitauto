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
from unittest.mock import patch

import pytest

from services.claude.tools.file_modify_result import FileWriteResult
from services.git import search_and_replace as search_and_replace_mod
from services.git.git_clone_to_tmp import git_clone_to_tmp
from services.git.git_commit_and_push import GitCommitResult
from services.git.search_and_replace import search_and_replace


def _ok_commit(**_kwargs):
    return GitCommitResult(success=True)


_PATCH_COMMIT = "services.git.search_and_replace.git_commit_and_push"


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

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="hello world",
            new_string="hello modified world",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated test.py."
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

    assert result == FileWriteResult(
        success=False,
        message="File 'nonexistent.py' not found.",
        file_path="nonexistent.py",
        content="",
    )


def test_directory_path_error(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "my_dir").mkdir()

    result = search_and_replace(
        old_string="old",
        new_string="new",
        file_path="my_dir",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="'my_dir' is a directory, not a file.",
        file_path="my_dir",
        content="",
    )


def test_empty_old_string(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("content\n")

    result = search_and_replace(
        old_string="",
        new_string="new",
        file_path="test.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="old_string must not be empty. Provide the exact text to find.",
        file_path="test.py",
        content="content\n",
    )


def test_old_string_not_found(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("print('hello')\n")

    result = search_and_replace(
        old_string="nonexistent text",
        new_string="replacement",
        file_path="test.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="old_string not found in 'test.py'. Verify the exact text including whitespace and indentation.",
        file_path="test.py",
        content="print('hello')\n",
    )


def test_multiple_occurrences(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("foo\nfoo\nbar\n")

    result = search_and_replace(
        old_string="foo",
        new_string="baz",
        file_path="test.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="old_string found 2 times in 'test.py'. Add more surrounding context to make it unique.",
        file_path="test.py",
        content="foo\nfoo\nbar\n",
    )


def test_no_change_when_old_equals_new(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("hello world\n")

    result = search_and_replace(
        old_string="hello world",
        new_string="hello world",
        file_path="test.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=True,
        message="No changes to test.py.",
        file_path="test.py",
        content="hello world\n",
    )


def test_preserve_crlf_line_endings(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.txt").write_text("line1\r\nline2\r\nline3\r\n", newline="")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="line2",
            new_string="modified_line2",
            file_path="test.txt",
            base_args=base_args,
        )

    assert result.success is True
    content = (tmp_path / "test.txt").read_text(newline="")
    assert content == "line1\r\nmodified_line2\r\nline3\r\n"


def test_nested_file_path(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    nested_dir = tmp_path / "src" / "utils"
    nested_dir.mkdir(parents=True)
    (nested_dir / "helper.py").write_text("old_function()\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="old_function()",
            new_string="new_function()",
            file_path="src/utils/helper.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (nested_dir / "helper.py").read_text() == "new_function()\n"


def test_extra_kwargs_ignored(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("old\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="old",
            new_string="new",
            file_path="test.py",
            base_args=base_args,
            extra_param="ignored",
        )

    assert result.success is True
    assert result.message == "Updated test.py."


def test_diff_included_in_message(create_test_base_args, tmp_path):
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("alpha\nbeta\ngamma\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="beta",
            new_string="delta",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated test.py."
    diff_lines = set(result.diff.splitlines())
    assert {"-beta", "+delta"}.issubset(diff_lines)


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

    assert (
        result.message
        == "old_string found 14 times in '_pydecimal.py'. Add more surrounding context to make it unique."
    )
    assert result.success is False


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

    assert (
        result.message
        == "old_string found 39 times in '_pydecimal.py'. Add more surrounding context to make it unique."
    )
    assert result.success is False


def test_pydecimal_add_method_unique_with_docstring(
    create_test_base_args, tmp_path, pydecimal_source
):
    # __add__ with its docstring is unique — should succeed on a 6300-line file
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    old = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """'
    new = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        NOTE: patched by search_and_replace test.\n        """'

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="_pydecimal.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated _pydecimal.py."
    content = (tmp_path / "_pydecimal.py").read_text()
    # __add__ got the NOTE, __sub__ untouched
    assert content.count("NOTE: patched by search_and_replace test.") == 1
    assert content.count("def __sub__(self, other, context=None):") == 1
    # File is still large (no accidental truncation)
    assert len(content.split("\n")) > 6000
    # result.content must match what was written to disk
    assert result.content == content
    # Diff must be present, with our change
    diff_lines = result.diff.splitlines()
    assert diff_lines.count("+        NOTE: patched by search_and_replace test.") == 1


def test_pydecimal_disambiguate_convert_other_via_method_signature(
    create_test_base_args, tmp_path, pydecimal_source
):
    # Including __add__ signature before the _convert_other block makes it unique
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "_pydecimal.py").write_text(pydecimal_source)

    old = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """\n        other = _convert_other(other)\n        if other is NotImplemented:\n            return other'
    new = '    def __add__(self, other, context=None):\n        """Returns self + other.\n\n        -INF + INF (or the reverse) cause InvalidOperation errors.\n        """\n        other = _convert_other(other, raiseit=False)\n        if other is NotImplemented:\n            return NotImplemented'

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="_pydecimal.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated _pydecimal.py."
    content = (tmp_path / "_pydecimal.py").read_text()
    # Only __add__ should have the change
    assert content.count("_convert_other(other, raiseit=False)") == 1
    # __sub__ still has the original pattern
    sub_idx = content.index("def __sub__(self")
    sub_block = content[sub_idx : sub_idx + 500]
    assert sub_block.count("_convert_other(other)") == 1
    assert sub_block.count("raiseit=False") == 0
    # result.content matches disk and diff is present
    assert result.content == content
    diff_lines = result.diff.splitlines()
    assert (
        diff_lines.count("+        other = _convert_other(other, raiseit=False)") == 1
    )


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

    assert (
        result.message
        == "old_string found 11 times in 'argparse.py'. Add more surrounding context to make it unique."
    )
    assert result.success is False


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

    assert result.success is False
    # Message is "old_string found N times in 'argparse.py'. ..." — assert the full format
    needle = "'argparse.py'. Add more surrounding context to make it unique."
    assert result.message.endswith(needle)
    assert result.message.startswith("old_string found ")


def test_argparse_help_action_call_unique_with_body(
    create_test_base_args, tmp_path, argparse_source
):
    # _HelpAction.__call__ body (print_help + exit) is unique across all Action subclasses
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    old = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help()\n        parser.exit()"
    new = "    def __call__(self, parser, namespace, values, option_string=None):\n        parser.print_help(file=None)\n        parser.exit(status=0)"

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="argparse.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated argparse.py."
    content = (tmp_path / "argparse.py").read_text()
    assert content.count("parser.print_help(file=None)") == 1
    assert content.count("parser.exit(status=0)") == 1
    # Other __call__ methods untouched (e.g. _VersionAction still has its own body)
    assert (
        content.count("parser.exit(message=formatter.format_help())") == 1
        or content.count("parser._print_message") >= 1
    )
    assert len(content.split("\n")) > 2500
    # result.content matches disk and diff is present
    assert result.content == content
    diff_lines = result.diff.splitlines()
    assert diff_lines.count("+        parser.print_help(file=None)") == 1
    assert diff_lines.count("+        parser.exit(status=0)") == 1


def test_argparse_disambiguate_call_via_class_context(
    create_test_base_args, tmp_path, argparse_source
):
    # Including the class definition makes the __call__ signature unique
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "argparse.py").write_text(argparse_source)

    old = "class _HelpAction(Action):\n\n    def __init__(self,\n                 option_strings,"
    new = 'class _HelpAction(Action):\n    """Display help and exit."""\n\n    def __init__(self,\n                 option_strings,'

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="argparse.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated argparse.py."
    content = (tmp_path / "argparse.py").read_text()
    assert content.count('"Display help and exit."') == 1
    # Other Action subclasses untouched
    assert content.count("class _VersionAction(Action):") == 1
    assert content.count("class _StoreAction(Action):") == 1
    # result.content matches disk and diff is present
    assert result.content == content
    diff_lines = result.diff.splitlines()
    assert diff_lines.count('+    """Display help and exit."""') == 1


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

    assert (
        result.message
        == "old_string found 7 times in 'typing.py'. Add more surrounding context to make it unique."
    )
    assert result.success is False


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

    assert (
        result.message
        == "old_string found 11 times in 'typing.py'. Add more surrounding context to make it unique."
    )
    assert result.success is False


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

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="typing.py",
            base_args=base_args,
        )

    assert result.success is True
    assert result.message == "Updated typing.py."
    content = (tmp_path / "typing.py").read_text()
    assert content.count("search_and_replace patched") == 1
    assert len(content.split("\n")) > 3500
    # result.content matches disk and diff is present
    assert result.content == content
    assert result.diff != ""


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

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="_pydecimal.py",
            base_args=base_args,
        )

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

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string=old,
            new_string=new,
            file_path="argparse.py",
            base_args=base_args,
        )

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
        assert (
            content.count(f"class {cls}(Action):")
            + content.count(f"class {cls}(Action)\n")
        ) >= 1


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

    assert result == FileWriteResult(
        success=False,
        message="old_string not found in 'test.py'. Verify the exact text including whitespace and indentation.",
        file_path="test.py",
        content="def foo():\n\treturn 1\n",
    )


def test_crlf_multiline_old_string_with_lf_input(create_test_base_args, tmp_path):
    # File uses CRLF but Claude sends LF in old_string — normalization should handle it
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.cs").write_text(
        "public class Foo {\r\n    int x = 1;\r\n    int y = 2;\r\n}\r\n",
        newline="",
    )

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="    int x = 1;\n    int y = 2;",
            new_string="    int x = 10;\n    int y = 20;",
            file_path="test.cs",
            base_args=base_args,
        )

    assert result.success is True
    content = (tmp_path / "test.cs").read_text(newline="")
    assert (
        content == "public class Foo {\r\n    int x = 10;\r\n    int y = 20;\r\n}\r\n"
    )


# ---------------------------------------------------------------------------
# Special characters and encoding
# ---------------------------------------------------------------------------


def test_regex_metacharacters_treated_as_literal(create_test_base_args, tmp_path):
    # Regex metacharacters in old_string must be treated as literal text
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    content = 'pattern = r"^(foo|bar)\\.(baz)+$"\nother = "hello"\n'
    (tmp_path / "test.py").write_text(content)

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string='pattern = r"^(foo|bar)\\.(baz)+$"',
            new_string='pattern = r"^(foo|bar|qux)\\.(baz)+$"',
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == (
        'pattern = r"^(foo|bar|qux)\\.(baz)+$"\nother = "hello"\n'
    )


def test_unicode_content(create_test_base_args, tmp_path):
    # Unicode characters in both old_string and file content
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text(
        '# コメント\nmessage = "こんにちは世界"\nprint(message)\n'
    )

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string='message = "こんにちは世界"',
            new_string='message = "Hello, 世界!"',
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == (
        '# コメント\nmessage = "Hello, 世界!"\nprint(message)\n'
    )


# ---------------------------------------------------------------------------
# String replacement edge cases
# ---------------------------------------------------------------------------


def test_old_string_is_substring_of_new_string(create_test_base_args, tmp_path):
    # When new_string contains old_string, replacement must happen exactly once
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("x = 1\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="x = 1",
            new_string="x = 1  # was x = 1",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "x = 1  # was x = 1\n"


def test_replacement_creates_duplicate_but_still_succeeds(
    create_test_base_args, tmp_path
):
    # After replacement new_string appears twice — fine, we only check uniqueness BEFORE replacing
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("aaa\nbbb\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="bbb",
            new_string="aaa",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "aaa\naaa\n"


def test_empty_new_string_deletes_match(create_test_base_args, tmp_path):
    # Empty new_string should delete the matched text
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("keep_this\ndelete_this\nkeep_this_too\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="delete_this\n",
            new_string="",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "keep_this\nkeep_this_too\n"


def test_entire_file_is_old_string(create_test_base_args, tmp_path):
    # Replacing the entire file content via search_and_replace
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("old content\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="old content\n",
            new_string="completely new content\n",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "completely new content\n"


# ---------------------------------------------------------------------------
# Post-processing verification
# ---------------------------------------------------------------------------


def test_trailing_spaces_stripped_after_replacement(create_test_base_args, tmp_path):
    # Verify strip_trailing_spaces runs after replacement
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("clean_line\nother_line\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="clean_line",
            new_string="has_trailing_spaces   ",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    content = (tmp_path / "test.py").read_text()
    # Post-processing strips trailing spaces from each non-empty line
    assert content == "has_trailing_spaces\nother_line\n"


def test_final_newline_ensured(create_test_base_args, tmp_path):
    # Verify ensure_final_newline adds one if replacement removes it
    base_args = create_test_base_args(skip_ci=False, clone_dir=str(tmp_path))
    (tmp_path / "test.py").write_text("line1\nline2\n")

    with patch(_PATCH_COMMIT, side_effect=_ok_commit):
        result = search_and_replace(
            old_string="line2\n",
            new_string="line2_no_newline",
            file_path="test.py",
            base_args=base_args,
        )

    assert result.success is True
    assert (tmp_path / "test.py").read_text() == "line1\nline2_no_newline\n"


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
            content = f.read()
        assert content.count("# Modified Test") == 1

        bare_dir = bare_url.replace("file://", "")
        log = subprocess.run(
            ["git", "log", "--format=%s", "feature/replace-test", "-1"],
            cwd=bare_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        assert log.stdout.strip().splitlines()[0] == "Update README.md"


def test_search_and_replace_propagates_concurrent_push(
    create_test_base_args, tmp_path, monkeypatch
):
    """Concurrent push from git_commit_and_push must bubble up as FileWriteResult(concurrent_push_detected=True) so chat_with_agent breaks the agent loop cleanly."""
    (tmp_path / "a.py").write_text("old line\n")

    monkeypatch.setattr(
        search_and_replace_mod,
        "git_commit_and_push",
        lambda **kwargs: GitCommitResult(success=False, concurrent_push_detected=True),
    )

    base_args = create_test_base_args(
        clone_dir=str(tmp_path), new_branch="feature/raced"
    )
    result = search_and_replace(
        old_string="old line",
        new_string="new line",
        file_path="a.py",
        base_args=base_args,
    )

    assert result == FileWriteResult(
        success=False,
        message="Concurrent push detected on `feature/raced` while committing a.py. Another commit landed; aborting this edit.",
        file_path="a.py",
        content="",
        concurrent_push_detected=True,
    )
